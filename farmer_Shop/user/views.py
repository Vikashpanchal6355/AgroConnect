from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Min, Max
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import uuid
import razorpay
from django.conf import settings
from .models import Contact_us, Category, Product, Cart, CartItem, Order, OrderItem, UserAddress, Wishlist
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
import logging

# Add logging to debug checkout issues
logger = logging.getLogger(__name__)

# Create your views here.


def _sync_order_to_myadmin(order):
    """Mirror a storefront order into myadmin so admins see it immediately."""
    try:
        from myadmin.models import (
            Category as AdminCategory,
            Product as AdminProduct,
            Order as AdminOrder,
            OrderItem as AdminOrderItem,
        )

        def sync_product(product):
            admin_category = None
            if product.category_id:
                admin_category, _ = AdminCategory.objects.update_or_create(
                    id=product.category_id,
                    defaults={
                        'name': product.category.name,
                        'description': getattr(product.category, 'description', None),
                    }
                )

            admin_product, _ = AdminProduct.objects.update_or_create(
                id=product.id,
                defaults={
                    'name': product.name,
                    'farmer': product.farmer,
                    'category': admin_category,
                    'description': product.description,
                    'additional_info': product.additional_info,
                    'reviews': product.reviews,
                    'price': product.price,
                    'original_price': product.original_price,
                    'image': product.image,
                    'rating': product.rating,
                    'is_new': product.is_new,
                    'is_hot': product.is_hot,
                    'is_sale': product.is_sale,
                    'stock': product.stock,
                    'view_count': product.view_count,
                    'sold_count': product.sold_count,
                    'sku': product.sku,
                    'tags': product.tags,
                }
            )
            return admin_product

        first_item = order.items.select_related('product').first()
        admin_order, _ = AdminOrder.objects.update_or_create(
            order_number=order.order_number,
            defaults={
                'user': order.user,
                'farmer': order.farmer or (first_item.product.farmer if first_item else None),
                'session_id': order.session_id,
                'first_name': order.first_name,
                'last_name': order.last_name,
                'email': order.email,
                'phone': order.phone,
                'address_line_1': order.address_line_1,
                'address_line_2': order.address_line_2,
                'city': order.city,
                'state': order.state,
                'postal_code': order.postal_code,
                'country': order.country,
                'status': order.status,
                'subtotal': order.subtotal,
                'shipping_cost': order.shipping_cost,
                'total': order.total,
                'payment_method': order.payment_method,
                'payment_status': order.payment_status,
                'razorpay_payment_id': order.razorpay_payment_id,
                'razorpay_order_id': order.razorpay_order_id,
                'notes': order.notes,
            }
        )

        admin_order.items.all().delete()
        for item in order.items.select_related('product'):
            AdminOrderItem.objects.create(
                order=admin_order,
                product=sync_product(item.product),
                quantity=item.quantity,
                price=item.price,
                subtotal=item.subtotal,
            )

        AdminOrder.objects.filter(pk=admin_order.pk).update(
            subtotal=order.subtotal,
            shipping_cost=order.shipping_cost,
            total=order.total,
        )
    except Exception:
        logger.exception("Unable to sync order %s to myadmin", order.order_number)


def _paginate_products(request, products, per_page=9):
    paginator = Paginator(products, per_page)
    page = request.GET.get('page', 1)

    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    return products_page, paginator, paginator.get_elided_page_range(products_page.number)


def _query_string_without_page(request):
    query_params = request.GET.copy()
    query_params.pop('page', None)
    encoded_params = query_params.urlencode()
    return f"&{encoded_params}" if encoded_params else ""


def index(request):
    # Get featured products for homepage
    featured_products = Product.objects.filter(is_new=True)[:8]
    # Get hot products
    hot_products = Product.objects.filter(is_hot=True)[:4]
    # Get sale products
    sale_products = Product.objects.filter(is_sale=True)[:4]
    # Get all categories
    categories = Category.objects.all()[:6]
    # Get popular products
    popular_products = Product.objects.order_by('-sold_count')[:8]

    # Check for login modal
    show_login_modal = request.session.pop('show_login_modal', False)
    
    return render(request, 'index.html', {
        'current_page': 'index',
        'featured_products': featured_products,
        'hot_products': hot_products,
        'sale_products': sale_products,
        'categories': categories,
        'popular_products': popular_products,
        'show_login_modal': show_login_modal,
    })

def about_us(request):
    return render(request, 'aboutus.html', {'current_page': 'about_us'})
def portfolio(request):
    return render(request, 'portfolio.html', {'current_page': 'portfolio'})

def portfolio_details(request):
    return render(request, 'portfolio-details.html', {'current_page': 'portfolio-details'}) 

def shop_products(request):
    categories = Category.objects.annotate(product_count=Count('product'))
    products = Product.objects.all()
    min_price = ''
    max_price = ''
    
    # Get price range for filter display
    min_price_range = products.aggregate(Min('price'))['price__min'] or 0
    max_price_range = products.aggregate(Max('price'))['price__max'] or 1000
    
    # Filter by category if provided
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filter by price if provided (either as min/max or price range)
    price_range = request.GET.get('price_range', '').strip()
    if price_range:
        # Handle price range like Amazon (e.g., "100-250")
        try:
            parts = price_range.split('-')
            if len(parts) == 2:
                min_price = parts[0]
                max_price = parts[1]
        except:
            pass
    else:
        # Use individual min_price and max_price if no range
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
    
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(name__icontains=search_query)

    sort_options = {
        'default': {
            'label': 'Default sorting',
            'ordering': ('-created_at',),
        },
        'latest': {
            'label': 'Latest products',
            'ordering': ('-created_at',),
        },
        'price_low_high': {
            'label': 'Price: Low to High',
            'ordering': ('price', 'name'),
        },
        'price_high_low': {
            'label': 'Price: High to Low',
            'ordering': ('-price', 'name'),
        },
        'popular': {
            'label': 'Popularity',
            'ordering': ('-sold_count', '-view_count', 'name'),
        },
        'rating': {
            'label': 'Average rating',
            'ordering': ('-rating', 'name'),
        },
        'name_az': {
            'label': 'Name: A to Z',
            'ordering': ('name',),
        },
    }
    current_sort = request.GET.get('sort', 'default')
    if current_sort not in sort_options:
        current_sort = 'default'

    products = products.order_by(*sort_options[current_sort]['ordering'])
    
    products_page, paginator, page_range = _paginate_products(request, products)
    
    # Get popular products (top 3 by sold_count)
    popular_products = Product.objects.order_by('-sold_count')[:3]
    
    context = {
        'current_page': 'shop',
        'categories': categories,
        'products': products_page,
        'popular_products': popular_products,
        'page_range': page_range,
        'paginator': paginator,
        'total_products_count': paginator.count,
        'search_query': search_query,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'min_price_range': int(min_price_range),
        'max_price_range': int(max_price_range),
        'sort_options': sort_options,
        'current_sort': current_sort,
        'current_sort_label': sort_options[current_sort]['label'],
        'query_string': _query_string_without_page(request),
    }
    return render(request, 'shop-products.html', context)

from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.utils.translation import activate, get_language_info
from django.conf import settings


def shop_details(request, pk=None):
    if pk is None:
        return redirect('shop_products')
    product = get_object_or_404(Product, pk=pk)
    # Get related products from the same category, excluding current product
    related_products = Product.objects.filter(category=product.category).exclude(pk=pk)[:6]
    # Get all categories with product counts
    categories = Category.objects.annotate(product_count=Count('product'))
    
    # Parse additional_info JSON if it exists
    additional_info_items = []
    if product.additional_info:
        import json
        try:
            info_dict = json.loads(product.additional_info)
            additional_info_items = info_dict.items()
        except (json.JSONDecodeError, AttributeError):
            pass
    
    # Parse reviews JSON if it exists
    reviews_list = []
    if product.reviews:
        import json
        try:
            reviews_list = json.loads(product.reviews)
        except (json.JSONDecodeError, AttributeError):
            pass
    
    context = {
        'current_page': 'shop',
        'product': product,
        'related_products': related_products,
        'categories': categories,
        'additional_info_items': list(additional_info_items),
        'reviews_list': reviews_list,
    }
    return render(request, 'shop-details.html', context)


@require_http_methods(["POST"])
def submit_review(request, product_id):
    """Handle review submission for a product"""
    product = get_object_or_404(Product, pk=product_id)
    
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    comment = request.POST.get('comment', '').strip()
    rating = request.POST.get('rating', '5').strip()
    
    if not name or not comment:
        return redirect('shop_details', pk=product_id)
    
    # Get existing reviews
    reviews_list = []
    if product.reviews:
        try:
            reviews_list = json.loads(product.reviews)
        except (json.JSONDecodeError, AttributeError):
            reviews_list = []
    
    # Add new review
    new_review = {
        'name': name,
        'date': timezone.now().strftime('%Y-%m-%d'),
        'comment': comment,
        'rating': int(rating) if rating else 5
    }
    reviews_list.append(new_review)
    
    # Save reviews back to product
    product.reviews = json.dumps(reviews_list)
    
    # Update product average rating
    if reviews_list:
        total_rating = sum(review.get('rating', 5) for review in reviews_list)
        product.rating = round(total_rating / len(reviews_list), 1)
    
    product.save()
    
    return redirect('shop_details', pk=product_id)


def shop_cart(request):
    # Get or create cart for session only if needed
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    
    # Get existing cart without creating new one
    cart = Cart.objects.filter(session_id=session_id).first()
    if cart and cart.items.exists():
        subtotal = sum(item.subtotal for item in cart.items.all())
        shipping_cost = 50 if subtotal < 500 else 0
        order_total = subtotal + shipping_cost
    else:
        cart = None
        subtotal = 0
        shipping_cost = 0
        order_total = 0

    context = {
        'current_page': 'shop',
        'cart': cart,
        'cart_subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'order_total': order_total,
    }
    return render(request, 'shop-cart.html', context)


def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        if not product_id:
            messages.error(request, 'Product not found.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        product = get_object_or_404(Product, id=product_id)
        
        # Get or create cart for session
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
        
        cart, created = Cart.objects.get_or_create(session_id=session_id)
        
        # Check if item already in cart
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not item_created:
            # Item exists, update quantity
            cart_item.quantity += quantity
            cart_item.save()
        
        messages.success(request, f'{product.name} added to cart!')
        return redirect('shop_cart')
    
    return redirect('shop_products')


def update_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        cart_item = get_object_or_404(CartItem, id=item_id)
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            # Refresh cart from database to get updated totals
            cart_item.cart.refresh_from_db()
            messages.success(request, 'Cart updated successfully.')
        else:
            cart_item.delete()
            messages.success(request, 'Item removed from cart.')
        
        return redirect('shop_cart')
    
    return redirect('shop_cart')


def update_cart_ajax(request):
    """AJAX view to update cart quantity and return JSON response"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
        
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart__session_id=session_id)
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Item not found in cart.'}, status=404)
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            cart_item.cart.refresh_from_db()
            cart_subtotal = float(cart_item.cart.total_price)
            shipping_cost = 50.0 if 0 < cart_subtotal < 500 else 0.0
            
            return JsonResponse({
                'success': True,
                'item_subtotal': float(cart_item.subtotal),
                'cart_subtotal': cart_subtotal,
                'shipping_cost': shipping_cost,
                'cart_total': cart_subtotal + shipping_cost,
                'item_id': item_id
            })
        else:
            cart_item.delete()
            cart_item.cart.refresh_from_db()
            cart_subtotal = float(cart_item.cart.total_price)
            shipping_cost = 50.0 if 0 < cart_subtotal < 500 else 0.0
            return JsonResponse({
                'success': True,
                'item_subtotal': 0,
                'cart_subtotal': cart_subtotal,
                'shipping_cost': shipping_cost,
                'cart_total': cart_subtotal + shipping_cost,
                'item_id': item_id,
                'deleted': True
            })
    
    return JsonResponse({'success': False}, status=400)


def remove_from_cart_ajax(request):
    """AJAX view to remove item from cart"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
        
        item_id = request.POST.get('item_id')
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart__session_id=session_id)
            product_name = cart_item.product.name
            cart_item.delete()
            
            # Get updated cart total
            try:
                cart = Cart.objects.get(session_id=session_id)
                cart_subtotal = float(cart.total_price)
                shipping_cost = 50.0 if 0 < cart_subtotal < 500 else 0.0
                cart_total = cart_subtotal + shipping_cost
            except Cart.DoesNotExist:
                cart_subtotal = 0
                shipping_cost = 0.0
                cart_total = 0
            
            return JsonResponse({
                'success': True,
                'cart_subtotal': cart_subtotal,
                'shipping_cost': shipping_cost,
                'cart_total': cart_total,
                'message': f'{product_name} removed from cart.'
            })
        except CartItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Item not found in cart.'
            }, status=404)
    
    return JsonResponse({'success': False}, status=400)


def remove_from_cart(request, item_id):
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__session_id=session_id)
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'{product_name} removed from cart.')
    except Exception as e:
        messages.error(request, 'Unable to remove item from cart.')
        print(f"Remove cart error: {e}")
    
    return redirect('shop_cart')


def empty_cart(request):
    """Remove all items from the cart"""
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    
    try:
        cart = Cart.objects.get(session_id=session_id)
        cart.items.all().delete()
        messages.success(request, 'Your cart has been emptied.')
    except Cart.DoesNotExist:
        pass
    
    return redirect('shop_cart')

def wishlist(request):
    # Ensure session exists for anonymous users
    if not request.user.is_authenticated and not request.session.session_key:
        request.session.create()
    
    # Get wishlist items
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    else:
        session_id = request.session.session_key
        if session_id:
            wishlist_items = Wishlist.objects.filter(session_id=session_id).select_related('product')
        else:
            wishlist_items = Wishlist.objects.none()
    
    context = {
        'current_page': 'shop',
        'wishlist_items': wishlist_items,
    }
    return render(request, 'wishlist.html', context)


def add_to_wishlist(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        
        if not product_id:
            messages.error(request, 'Product not found')
            return redirect(request.META.get('HTTP_REFERER', 'index'))
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            messages.error(request, 'Product not found')
            return redirect(request.META.get('HTTP_REFERER', 'index'))
        
        # Check if already in wishlist
        if request.user.is_authenticated:
            existing = Wishlist.objects.filter(user=request.user, product=product).first()
        else:
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key
            existing = Wishlist.objects.filter(session_id=session_id, product=product).first()
        
        if existing:
            messages.info(request, 'Product already in wishlist')
        else:
            if request.user.is_authenticated:
                Wishlist.objects.create(user=request.user, product=product)
            else:
                Wishlist.objects.create(session_id=session_id, product=product)
            messages.success(request, 'Product added to wishlist')
    
    return redirect(request.META.get('HTTP_REFERER', 'index'))


def remove_from_wishlist(request, wishlist_id):
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()
    
    try:
        wishlist_item = Wishlist.objects.get(id=wishlist_id)
        
        # Check if user owns this wishlist item
        if request.user.is_authenticated:
            if wishlist_item.user != request.user:
                messages.error(request, 'You do not have permission to remove this item')
                return redirect('wishlist')
        else:
            session_id = request.session.session_key
            if wishlist_item.session_id != session_id:
                messages.error(request, 'You do not have permission to remove this item')
                return redirect('wishlist')
        
        product_name = wishlist_item.product.name
        wishlist_item.delete()
        messages.success(request, f'{product_name} removed from wishlist')
    except Wishlist.DoesNotExist:
        messages.error(request, 'Item not found in wishlist')
    
    return redirect('wishlist')

def empty_wishlist(request):
    """Remove all items from the wishlist"""
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    
    try:
        if request.user.is_authenticated:
            Wishlist.objects.filter(user=request.user).delete()
        else:
            Wishlist.objects.filter(session_id=session_id).delete()
        messages.success(request, 'Your wishlist has been cleared.')
    except Exception as e:
        messages.error(request, 'Unable to clear wishlist.')
        print(f"Empty wishlist error: {e}")
    
    return redirect('wishlist')

def checkout(request):
    # Check if user is authenticated
    # Get or create cart for session
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    
    # Check if this is a Razorpay payment callback
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    
    # Handle successful payment callback from Razorpay
    if razorpay_payment_id and razorpay_order_id and request.method == 'POST':
        print(f"Processing Razorpay callback - payment_id: {razorpay_payment_id}, order_id: {razorpay_order_id}")
        
        # Get pending order from session
        pending_order = request.session.get('pending_order')
        
        if not pending_order:
            # Try to find existing order
            existing_order = Order.objects.filter(razorpay_payment_id=razorpay_payment_id).first()
            if existing_order:
                messages.success(request, f'Your order #{existing_order.order_number} has been placed successfully!')
                return redirect('order_confirmation', order_id=existing_order.id)
            messages.error(request, 'Order processing issue. Please contact support.')
            return redirect('shop_cart')
        
        try:
            # Get cart
            try:
                cart = Cart.objects.get(session_id=session_id)
            except Cart.DoesNotExist:
                messages.error(request, 'Cart not found. Please contact support.')
                return redirect('shop_cart')
            
            # Create the order
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id,
                first_name=pending_order.get('first_name', ''),
                last_name=pending_order.get('last_name', ''),
                email=pending_order.get('email', ''),
                phone=pending_order.get('phone', ''),
                address_line_1=pending_order.get('address_line_1', ''),
                address_line_2=pending_order.get('address_line_2', ''),
                city=pending_order.get('city', ''),
                state=pending_order.get('state', ''),
                postal_code=pending_order.get('postal_code', ''),
                country=pending_order.get('country', 'India'),
                subtotal=pending_order.get('subtotal', 0),
                shipping_cost=pending_order.get('shipping_cost', 0),
                total=pending_order.get('total', 0),
                payment_method=pending_order.get('payment_method', 'online'),
                notes=pending_order.get('notes', ''),
                status='processing',
                payment_status='completed',
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id
            )
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    subtotal=cart_item.subtotal
                )
                
                # Update product stock
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.sold_count += cart_item.quantity
                cart_item.product.save()
            
            _sync_order_to_myadmin(order)

            # Clear the cart and pending order
            cart.items.all().delete()
            cart.delete()
            request.session.pop('pending_order', None)
            
            print(f"Order created: {order.order_number}, redirecting to confirmation")
            messages.success(request, f'Your order #{order.order_number} has been placed successfully!')
            return redirect('order_confirmation', order_id=order.id)
            
        except Exception as e:
            print(f"Error processing payment: {e}")
            messages.error(request, 'Payment processing failed. Please contact support.')
            return redirect('shop_cart')
    
    # Normal checkout - get cart
    try:
        cart = Cart.objects.get(session_id=session_id)
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty.')
        return redirect('shop_cart')
    
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('shop_cart')
    
    # Handle form submission for non-Razorpay payments
    if request.method == 'POST':
        # Get customer info
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # Get shipping address
        address_line_1 = request.POST.get('address_line_1', '').strip()
        address_line_2 = request.POST.get('address_line_2', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', 'India').strip()
        
        # Payment info
        payment_method = request.POST.get('payment_method', 'cod')
        notes = request.POST.get('notes', '').strip()
        
        # Validation
        errors = []
        if not first_name: errors.append('First name is required.')
        if not last_name: errors.append('Last name is required.')
        if not email: errors.append('Email is required.')
        if not phone: errors.append('Phone number is required.')
        if not address_line_1: errors.append('Address is required.')
        if not city: errors.append('City is required.')
        if not state: errors.append('State is required.')
        if not postal_code: errors.append('Postal code is required.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            # Re-render checkout with form data
            context = {
                'current_page': 'shop',
                'cart': cart,
                'form_data': request.POST,
            }
            if request.user.is_authenticated:
                context['user'] = request.user
                context['addresses'] = UserAddress.objects.filter(user=request.user)
            return render(request, 'checkout.html', context)
        
        # Calculate totals
        subtotal = cart.total_price
        shipping_cost = 50 if subtotal < 500 else 0
        total = subtotal + shipping_cost
        
        # Handle online payment (Razorpay)
        if payment_method in ('online', 'upi'):
            try:
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                amount_in_paise = int(total * 100)
                
                razorpay_order = client.order.create({
                    'amount': amount_in_paise,
                    'currency': 'INR',
                    'payment_capture': 1
                })
                
                # Store order details in session
                request.session['pending_order'] = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone': phone,
                    'address_line_1': address_line_1,
                    'address_line_2': address_line_2,
                    'city': city,
                    'state': state,
                    'postal_code': postal_code,
                    'country': country,
                    'subtotal': str(subtotal),
                    'shipping_cost': str(shipping_cost),
                    'total': str(total),
                    'notes': notes,
                    'payment_method': payment_method,
                    'razorpay_order_id': razorpay_order['id']
                }
                
                context = {
                    'current_page': 'shop',
                    'cart': cart,
                    'razorpay_order_id': razorpay_order['id'],
                    'razorpay_key': settings.RAZORPAY_KEY_ID,
                    'total_amount': total,
                    'customer_name': f"{first_name} {last_name}",
                    'customer_email': email,
                    'customer_phone': phone,
                    'selected_payment_method': payment_method,
                }
                
                if request.user.is_authenticated:
                    context['user'] = request.user
                    context['addresses'] = UserAddress.objects.filter(user=request.user)
                
                return render(request, 'checkout.html', context)
                
            except Exception as e:
                print(f"Razorpay order creation error: {e}")
                messages.error(request, 'Failed to initiate payment. Please try again or use Cash on Delivery.')
                return redirect('checkout')
        
        # Handle COD
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_id=session_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total=total,
            payment_method=payment_method,
            notes=notes,
            status='pending',
            payment_status='pending'
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                subtotal=cart_item.subtotal
            )
            
            # Update product stock
            cart_item.product.stock -= cart_item.quantity
            cart_item.product.sold_count += cart_item.quantity
            cart_item.product.save()
        
        _sync_order_to_myadmin(order)

        # Clear the cart
        cart.items.all().delete()
        cart.delete()
        
        messages.success(request, f'Your order #{order.order_number} has been placed successfully!')
        return redirect('order_confirmation', order_id=order.id)
    
    # GET request - show checkout form
    context = {
        'current_page': 'shop',
        'cart': cart,
    }
    
    if request.user.is_authenticated:
        context['user'] = request.user
        context['addresses'] = UserAddress.objects.filter(user=request.user).order_by('-is_default', '-created_at')
        
        # Auto-fill form with default address
        default_address = UserAddress.objects.filter(user=request.user, is_default=True).first()
        if not default_address:
            default_address = UserAddress.objects.filter(user=request.user).order_by('-created_at').first()
        
        if default_address:
            context['default_address'] = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'address_line_1': default_address.address_line_1,
                'address_line_2': default_address.address_line_2 or '',
                'city': default_address.city,
                'state': default_address.state,
                'postal_code': default_address.postal_code,
                'country': default_address.country,
                'phone': default_address.phone or '',
            }
        else:
            context['default_address'] = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'address_line_1': '',
                'address_line_2': '',
                'city': '',
                'state': '',
                'postal_code': '',
                'country': 'India',
                'phone': '',
            }
    
    return render(request, 'checkout.html', context)


def order_confirmation(request, order_id):
    """Display order confirmation page"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user owns this order or has the session
    if request.user.is_authenticated:
        if order.user and order.user != request.user:
            messages.error(request, 'You do not have permission to view this order.')
            return redirect('index')
    else:
        if not request.session.session_key or order.session_id != request.session.session_key:
            messages.error(request, 'Invalid order.')
            return redirect('index')
    
    context = {
        'current_page': 'shop',
        'order': order,
    }
    return render(request, 'order-confirmation.html', context)


def _user_can_access_order(request, order):
    """Return True when the current user or session owns the order."""
    if request.user.is_authenticated:
        return order.user == request.user
    return bool(request.session.session_key and order.session_id == request.session.session_key)

def order_tracking(request):
    order = None
    order_items = None
    error_message = None
    
    if request.method == 'POST':
        order_id = request.POST.get('orderid', '').strip()
        order_email = request.POST.get('order_email', '').strip()
        
        if order_id and order_email:
            try:
                # Try to find order by order_number and email
                order = Order.objects.get(order_number=order_id, email=order_email)
                order_items = OrderItem.objects.filter(order=order)
            except Order.DoesNotExist:
                error_message = 'Order not found. Please check your Order ID and email address.'
        else:
            error_message = 'Please enter both Order ID and email address.'
    
    context = {
        'current_page': 'shop',
        'order': order,
        'order_items': order_items,
        'error_message': error_message,
    }
    return render(request, 'order-tracking.html', context)

def my_account(request):
    if not request.user.is_authenticated:
        return redirect('login')
    context = {
        'current_page': 'shop',
        'orders_count': Order.objects.filter(user=request.user).count(),
        'addresses_count': UserAddress.objects.filter(user=request.user).count(),
        'wishlist_count': Wishlist.objects.filter(user=request.user).count(),
    }
    return render(request, 'my-account.html', context)

def my_account_orders(request):
    if not request.user.is_authenticated:
        return redirect('login')
    # Get orders for the logged-in user
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my-account-orders.html', {'current_page': 'shop', 'orders': user_orders})

def my_account_address(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        address_line_1 = request.POST.get('address_line_1', '').strip()
        address_line_2 = request.POST.get('address_line_2', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', 'India').strip() or 'India'
        phone = request.POST.get('phone', '').strip()
        is_default = request.POST.get('is_default') in {'on', 'true', '1'}

        if is_default:
            UserAddress.objects.filter(user=request.user).update(is_default=False)

        if address_id:
            address = get_object_or_404(UserAddress, id=address_id, user=request.user)
            address.first_name = first_name
            address.last_name = last_name
            address.address_line_1 = address_line_1
            address.address_line_2 = address_line_2
            address.city = city
            address.state = state
            address.postal_code = postal_code
            address.country = country
            address.phone = phone
            address.is_default = is_default
            address.save()
            messages.success(request, 'Address updated successfully.')
        else:
            UserAddress.objects.create(
                user=request.user,
                first_name=first_name,
                last_name=last_name,
                address_line_1=address_line_1,
                address_line_2=address_line_2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
                phone=phone,
                is_default=is_default
            )
            messages.success(request, 'Address added successfully.')
        return redirect('my_account_address')
    
    addresses = UserAddress.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    editing_address = None
    edit_address_id = request.GET.get('edit')

    if edit_address_id:
        editing_address = get_object_or_404(UserAddress, id=edit_address_id, user=request.user)

    return render(
        request,
        'my-account-address.html',
        {
            'current_page': 'shop',
            'addresses': addresses,
            'editing_address': editing_address,
        }
    )


def delete_address(request, address_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        address = UserAddress.objects.get(id=address_id, user=request.user)
        address.delete()
        messages.success(request, 'Address deleted successfully.')
    except UserAddress.DoesNotExist:
        messages.error(request, 'Address not found.')
    
    return redirect('my_account_address')

def my_account_edit(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Update user info
        user = request.user
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if email:
            user.email = email
        user.save()
        
        # Update password if provided
        if current_password and new_password and confirm_password:
            if user.check_password(current_password):
                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, 'Password updated successfully. Please login again.')
                else:
                    messages.error(request, 'New passwords do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')
        else:
            messages.success(request, 'Account details updated successfully.')
        
        return redirect('my_account_edit')
    
    return render(request, 'my-account-edit.html', {'current_page': 'shop'})

def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not _user_can_access_order(request, order):
        messages.error(request, 'You do not have permission to view this order.')
        return redirect('index')
    order_items = order.items.all()
    return render(request, 'order-details.html', {
        'current_page': 'shop',
        'order': order,
        'order_items': order_items
    })

def print_receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not _user_can_access_order(request, order):
        messages.error(request, 'You do not have permission to view this receipt.')
        return redirect('index')
    order_items = order.items.all()
    return render(request, 'print-receipt.html', {
        'order': order,
        'order_items': order_items
    })

def our_services(request):
    return render(request, 'our-services.html', {'current_page': 'our_services'})

def service_detail(request):
    return render(request, 'service-detail.html', {'current_page': 'service_detail'})

def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        
        if name and email and phone and message:
            try:
                # Save to database
                Contact_us.objects.create(
                    name=name,
                    email=email,
                    phone=phone,
                    message=message
                )
                
                messages.success(request, 'Your message has been sent successfully!')
            except Exception as e:
                messages.error(request, 'Error saving message. Please try again.')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'contact-us.html', {'current_page': 'contact_us'})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember', False)
        
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Only allow non-staff users to log in on the website
            # Admin/Staff users must use Django admin (/admin/)
            if user.is_staff or user.is_superuser:
                messages.error(request, 'Admin users must log in through the admin panel. Please use /admin/')
                return redirect(request.META.get('HTTP_REFERER', '/'))
            
            login(request, user)
            
            if not remember_me:
                request.session.set_expiry(0)  
            else:
                request.session.set_expiry(30 * 24 * 60 * 60)  
            
            messages.success(request, f'Welcome back, {user.first_name or username}!')
            return redirect('/')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
    
    return redirect('/')


def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        role = request.POST.get('role', 'customer').strip().lower()
        farmer_name = request.POST.get('farmer_name', '').strip()
        farmer_phone = request.POST.get('farmer_phone', '').strip()
        farmer_address = request.POST.get('farmer_address', '').strip()
        
        errors = []
        valid_roles = {'customer', 'farmer'}
        
        if role not in valid_roles:
            errors.append('Please select a valid role.')

        if not username:
            errors.append('Username is required.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists. Please choose a different username.')
        
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        if not password:
            errors.append('Password is required.')
        
        if password != password_confirm:
            errors.append('Passwords do not match.')

        if role == 'farmer':
            if not farmer_name:
                errors.append('Farmer name is required.')
            if not farmer_phone:
                errors.append('Farmer phone is required.')
        
        # Show errors if any
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Create user
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=farmer_name if role == 'farmer' else '',
                    is_staff=role == 'farmer',
                    is_superuser=role == 'farmer',
                )

                if role == 'farmer':
                    from myadmin.models import Farmer

                    Farmer.objects.create(
                        user=user,
                        name=farmer_name,
                        phone=farmer_phone,
                        address=farmer_address,
                    )
            
            # Log the user in after registration
            login(request, user)
            if role == 'farmer':
                messages.success(request, f'Farmer account created successfully! Welcome, {farmer_name or username}!')
                return redirect('/myadmin/')

            messages.success(request, f'Account created successfully! Welcome, {username}!')
            return redirect('/')
            
        except IntegrityError:
            messages.error(request, 'An error occurred during registration. Please try again.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
    
    return redirect('/')


@login_required(login_url='index')
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('/')


def search_products(request):
    """Search products by name or description"""
    query = request.GET.get('q', '')
    categories = Category.objects.annotate(product_count=Count('product'))
    all_products = Product.objects.all()
    min_price_range = all_products.aggregate(Min('price'))['price__min'] or 0
    max_price_range = all_products.aggregate(Max('price'))['price__max'] or 1000
    popular_products = Product.objects.order_by('-sold_count')[:3]
    
    if query:
        # Search in product name and description
        products = Product.objects.filter(
            name__icontains=query
        ) | Product.objects.filter(
            description__icontains=query
        )
        products = products.order_by('-created_at').distinct()
    else:
        products = Product.objects.none()

    products_page, paginator, page_range = _paginate_products(request, products)

    context = {
        'current_page': 'shop',
        'categories': categories,
        'products': products_page,
        'popular_products': popular_products,
        'search_query': query,
        'page_range': page_range,
        'paginator': paginator,
        'total_products_count': paginator.count,
        'min_price': '',
        'max_price': '',
        'min_price_range': int(min_price_range),
        'max_price_range': int(max_price_range),
    }
    return render(request, 'shop-products.html', context)


def razorpay_callback(request):
    """Handle Razorpay payment callback"""
    if request.method == 'POST':
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        # Get pending order details from session
        pending_order = request.session.get('pending_order')
        
        if not pending_order:
            messages.error(request, 'Order not found. Please contact support.')
            return redirect('shop_cart')
        
        try:
            # Verify the payment signature
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            # Get or create cart
            if not request.session.session_key:
                request.session.create()
            session_id = request.session.session_key
            cart = get_object_or_404(Cart, session_id=session_id)
            
            # Create order with verified payment
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id,
                first_name=pending_order.get('first_name'),
                last_name=pending_order.get('last_name'),
                email=pending_order.get('email'),
                phone=pending_order.get('phone'),
                address_line_1=pending_order.get('address_line_1'),
                address_line_2=pending_order.get('address_line_2', ''),
                city=pending_order.get('city'),
                state=pending_order.get('state'),
                postal_code=pending_order.get('postal_code'),
                country=pending_order.get('country', 'India'),
                subtotal=pending_order.get('subtotal'),
                shipping_cost=pending_order.get('shipping_cost'),
                total=pending_order.get('total'),
                payment_method=pending_order.get('payment_method', 'online'),
                notes=pending_order.get('notes', ''),
                status='processing',
                payment_status='completed',
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id
            )
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    subtotal=cart_item.subtotal
                )
                
                # Update product stock
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.sold_count += cart_item.quantity
                cart_item.product.save()
            
            _sync_order_to_myadmin(order)

            # Clear the cart and pending order
            cart.items.all().delete()
            cart.delete()
            request.session.pop('pending_order', None)
            
            messages.success(request, f'Your order #{order.order_number} has been placed successfully!')
            return redirect('order_confirmation', order_id=order.id)
            
        except Exception as e:
            print(f"Razorpay callback error: {e}")
            messages.error(request, 'Payment verification failed. Please contact support.')
            return redirect('checkout')
    
    # If GET request, redirect to checkout
    return redirect('checkout')


def set_language(request):
    """Switch language and redirect back to previous page"""
    language = request.GET.get('language', 'en')
    next_url = request.GET.get('next', '/')
    
    # Validate language code
    available_languages = [lang[0] for lang in settings.LANGUAGES]
    if language not in available_languages:
        language = 'en'
    
    # Activate the language
    activate(language)
    
    # Set language in session (using hardcoded key)
    request.session['_language'] = language
    
    # Redirect to the previous page or home
    return redirect(next_url)








