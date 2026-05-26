from functools import wraps
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models.functions import TruncDate
from django.utils import timezone
from .models import *


def is_myadmin_user(user):
    return user.is_authenticated and (user.is_superuser or hasattr(user, 'farmer_profile'))

def myadmin_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/myadmin/login/?next={request.get_full_path()}")

        if not is_myadmin_user(request.user):
            messages.error(request, 'Please log in with an admin or farmer account.')
            return redirect('/myadmin/login/')

        return view_func(request, *args, **kwargs)
    return _wrapped_view

def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'Only super admins can manage users.')
            return redirect('myadmin:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def login_view(request):
    if is_myadmin_user(request.user):
        return redirect('/myadmin/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or '/myadmin/'
        user = authenticate(request, username=username, password=password)
        if user and is_myadmin_user(user):
            login(request, user)
            return redirect(next_url)
        messages.error(request, 'Invalid login for admin.')
    context = {
        'next_url': request.GET.get('next', '/myadmin/'),
    }
    return render(request, 'myadmin/simple-login.html', context)

def logout_view(request):
    logout(request)
    return redirect('/myadmin/login/')


def dashboard(request):
    if hasattr(request.user, 'farmer_profile') and not request.user.is_superuser:
        # Farmer logged in - show only own data
        own_farmer = request.user.farmer_profile
        farmer_id = str(own_farmer.id)
        filter_kwargs = {'farmer_id': farmer_id}
        farmers = []  # Don't show farmers dropdown
        is_farmer = True
    else:
        # Superadmin - can see all
        farmer_id = request.GET.get('farmer_id')
        filter_kwargs = {}
        if farmer_id:
            filter_kwargs['farmer_id'] = farmer_id
        farmers = Farmer.objects.filter(is_active=True)
        is_farmer = False
    
    total_products = Product.objects.filter(**filter_kwargs).count()
    total_orders = Order.objects.filter(**filter_kwargs).count()
    total_revenue = Order.objects.filter(**filter_kwargs, status='delivered').aggregate(total=Sum('total'))['total'] or 0
    recent_orders = Order.objects.filter(**filter_kwargs).order_by('-created_at')[:5]
    pending_orders = Order.objects.filter(**filter_kwargs, status='pending').count()
    delivered_orders = Order.objects.filter(**filter_kwargs, status='delivered').count()
    cancelled_orders = Order.objects.filter(**filter_kwargs, status='cancelled').count()
    processing_orders = Order.objects.filter(**filter_kwargs, status='processing').count()
    total_users = User.objects.count() if request.user.is_superuser else 1
    total_farmers = Farmer.objects.filter(is_active=True).count() if request.user.is_superuser else 1
    low_stock_products = Product.objects.filter(**filter_kwargs, stock__lte=5).count()

    today = timezone.localdate()
    last_7_days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    revenue_rows = (
        Order.objects.filter(
            **filter_kwargs,
            status='delivered',
            created_at__date__gte=last_7_days[0],
        )
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Sum('total'))
        .order_by('day')
    )
    revenue_map = {row['day']: float(row['total'] or 0) for row in revenue_rows}
    weekly_revenue_series = [
        {
            'label': day.strftime('%d %b'),
            'value': revenue_map.get(day, 0),
        }
        for day in last_7_days
    ]

    order_status_series = [
        {'label': 'Pending', 'value': pending_orders},
        {'label': 'Processing', 'value': processing_orders},
        {'label': 'Delivered', 'value': delivered_orders},
        {'label': 'Cancelled', 'value': cancelled_orders},
    ]

    top_category_rows = (
        Product.objects.filter(**filter_kwargs)
        .values('category__name')
        .annotate(total=Count('id'))
        .order_by('-total', 'category__name')[:5]
    )
    top_category_series = [
        {
            'label': row['category__name'] or 'Uncategorized',
            'value': row['total'],
        }
        for row in top_category_rows
    ]
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'processing_orders': processing_orders,
        'total_users': total_users,
        'total_farmers': total_farmers,
        'low_stock_products': low_stock_products,
        'farmers': farmers,
        'selected_farmer': farmer_id,
        'is_farmer': is_farmer,
        'weekly_revenue_series': weekly_revenue_series,
        'order_status_series': order_status_series,
        'top_category_series': top_category_series,
    }
    return render(request, 'myadmin/simple-dashboard.html', context)


def products(request):
    # Get the logged-in farmer's profile
    farmer = None
    
    farmer_id = request.GET.get('farmer_id')
    products = Product.objects.all().order_by('-id')
    
    # Filter by logged-in farmer if not superuser
    if farmer and not request.user.is_superuser:
        products = products.filter(farmer=farmer)
    elif farmer_id and request.user.is_superuser:
        products = products.filter(farmer_id=farmer_id)
    
    categories = Category.objects.all()
    farmers = Farmer.objects.filter(is_active=True)
    paginator = Paginator(products, 25)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    context = {
        'products': products,
        'categories': categories,
        'farmers': farmers,
        'selected_farmer': farmer_id,
    }
    return render(request, 'myadmin/simple-products.html', context)


def add_product(request):
    categories = Category.objects.all()
    
    # Get the logged-in farmer's profile
    farmer = None
    
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        # simplified
        category = Category.objects.get(id=category_id) if category_id else None
        Product.objects.create(name=name, category=category, price=price, farmer=farmer)
        messages.success(request, f'Product "{name}" added!')
        return HttpResponseRedirect('/myadmin/products/')
    context = {'categories': categories}
    return render(request, 'myadmin/add_product.html', context)


def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if farmer can edit this product
    
    # If not superuser and product belongs to different farmer, deny access
    if farmer and not request.user.is_superuser and product.farmer_id != farmer.id:
        messages.error(request, 'You can only edit your own products.')
        return HttpResponseRedirect('/myadmin/products/')
    
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        category = Category.objects.get(id=category_id) if category_id else None
        product.name = name
        product.category = category
        product.price = price
        product.save()
        messages.success(request, 'Product updated!')
        return HttpResponseRedirect('/myadmin/products/')
    context = {'product': product, 'categories': categories}
    return render(request, 'myadmin/edit_product.html', context)


def update_product(request, product_id):
    return edit_product(request, product_id)


def delete_product(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        
        # Check if farmer can delete this product

        
        # If not superuser and product belongs to different farmer, deny access
        if farmer and not request.user.is_superuser and product.farmer_id != farmer.id:
            messages.error(request, 'You can only delete your own products.')
        else:
            product.delete()
            messages.success(request, 'Product deleted!')
    return HttpResponseRedirect('/myadmin/products/')


def categories(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'category_product_total': Product.objects.count(),
    }
    return render(request, 'myadmin/categories.html', context)


def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        Category.objects.create(name=name)
        messages.success(request, 'Category added!')
        return HttpResponseRedirect('/myadmin/categories/')
    return render(request, 'myadmin/add_category.html')


def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        category.name = name
        category.save()
        messages.success(request, 'Category updated!')
        return HttpResponseRedirect('/myadmin/categories/')
    context = {'category': category}
    return render(request, 'myadmin/edit_category.html', context)


def delete_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        category.delete()
        messages.success(request, 'Category deleted!')
    return HttpResponseRedirect('/myadmin/categories/')


def orders(request):
    # Get the logged-in farmer's profile
    farmer = None
    
    
    farmer_id = request.GET.get('farmer_id')
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip().lower()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    orders = Order.objects.all().order_by('-created_at')
    
    # Filter by logged-in farmer if not superuser
    if farmer and not request.user.is_superuser:
        orders = orders.filter(farmer=farmer)
    elif farmer_id and request.user.is_superuser:
        orders = orders.filter(farmer_id=farmer_id)
    
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    if status_filter:
        orders = orders.filter(status=status_filter)

    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)

    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)

    farmers = Farmer.objects.filter(is_active=True)
    stats_orders = orders
    paginator = Paginator(orders, 25)
    page = request.GET.get('page', 1)
    orders_page = paginator.get_page(page)
    context = {
        'orders': orders_page,
        'farmers': farmers,
        'selected_farmer': farmer_id,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_orders': stats_orders.count(),
        'pending_orders': stats_orders.filter(status='pending').count(),
        'delivered_orders': stats_orders.filter(status='delivered').count(),
        'processing_orders': stats_orders.filter(status='processing').count(),
        'cancelled_orders': stats_orders.filter(status='cancelled').count(),
        'total_revenue': stats_orders.filter(status='delivered').aggregate(total=Sum('total'))['total'] or 0,
    }
    return render(request, 'myadmin/simple-orders.html', context)


def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status', '').strip().lower()
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        if new_status in valid_statuses:
            order.status = new_status
            order.save()

            try:
                from user.models import Order as UserOrder

                UserOrder.objects.filter(order_number=order.order_number).update(
                    status=new_status,
                    updated_at=timezone.now(),
                )
            except Exception:
                return JsonResponse({
                    'success': False,
                    'error': 'Admin order updated, but user order sync failed.'
                })

            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Invalid status.'})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@superuser_required
def users(request):
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
        'superuser_count': users.filter(is_superuser=True).count(),
        'active_user_count': users.filter(is_active=True).count(),
    }
    return render(request, 'myadmin/users.html', context)


@superuser_required
def edit_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '').strip()

        if not username:
            messages.error(request, 'Username is required.')
            return render(request, 'myadmin/edit_user.html', {'user_obj': user_obj})

        if User.objects.filter(username=username).exclude(id=user_obj.id).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'myadmin/edit_user.html', {'user_obj': user_obj})

        user_obj.username = username
        user_obj.email = email
        user_obj.first_name = first_name
        user_obj.last_name = last_name
        if user_obj.id == request.user.id:
            user_obj.is_active = True
            user_obj.is_staff = True
            user_obj.is_superuser = True
        else:
            user_obj.is_active = request.POST.get('is_active') == 'on'
            user_obj.is_superuser = request.POST.get('is_superuser') == 'on'
            user_obj.is_staff = user_obj.is_superuser
        if password:
            user_obj.set_password(password)
        user_obj.save()
        messages.success(request, 'User updated!')
        return redirect('myadmin:users')

    return render(request, 'myadmin/edit_user.html', {'user_obj': user_obj})


@superuser_required
def delete_user(request, user_id):
    if request.method == 'POST':
        user_obj = get_object_or_404(User, id=user_id)
        if user_obj.id == request.user.id:
            messages.error(request, 'You cannot delete your own account.')
        else:
            user_obj.delete()
            messages.success(request, 'User deleted!')
    return redirect('myadmin:users')


def contacts(request):
    contacts = Contact_us.objects.all().order_by('-created_at')
    context = {'contacts': contacts}
    return render(request, 'myadmin/contacts.html', context)


def mark_contact_read(request, contact_id):
    contact = get_object_or_404(Contact_us, id=contact_id)
    contact.is_read = True
    contact.save()
    messages.success(request, 'Contact marked as read.')
    return HttpResponseRedirect('/myadmin/contacts/')


def wishlists(request):
    wishlists = Wishlist.objects.all().order_by('-created_at')
    context = {'wishlists': wishlists}
    return render(request, 'myadmin/wishlists.html', context)


def carts(request):
    carts = Cart.objects.all().order_by('-updated_at')
    context = {'carts': carts}
    return render(request, 'myadmin/carts.html', context)


def addresses(request):
    addresses = UserAddress.objects.all().order_by('-id')
    context = {'addresses': addresses}
    return render(request, 'myadmin/addresses.html', context)


def settings(request):
    settings_obj, created = SiteSettings.objects.get_or_create(id=1)
    if request.method == 'POST':
        settings_obj.notification_banner = request.POST.get('notification_banner')
        settings_obj.is_notification_active = request.POST.get('is_notification_active') == 'on'
        settings_obj.save()
        messages.success(request, 'Settings saved!')
    context = {'site_settings': settings_obj}
    return render(request, 'myadmin/settings.html', context)


def farmers(request):
    farmers = Farmer.objects.select_related('user').order_by('-created_at')
    context = {
        'farmers': farmers,
        'active_farmer_count': farmers.filter(is_active=True).count(),
    }
    return render(request, 'myadmin/farmers.html', context)


def add_farmer(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address', '')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username exists.')
            return render(request, 'myadmin/add_farmer.html')
        user = User.objects.create_user(username=username, email=email, password=password, is_staff=True, is_superuser=True)
        Farmer.objects.create(user=user, name=name, phone=phone, address=address)
        messages.success(request, 'Farmer created!')
        return redirect('myadmin:farmers')
    return render(request, 'myadmin/add_farmer.html')


def edit_farmer(request, farmer_id):
    farmer = get_object_or_404(Farmer, id=farmer_id)
    if request.method == 'POST':
        farmer.name = request.POST.get('name')
        farmer.phone = request.POST.get('phone')
        farmer.address = request.POST.get('address')
        farmer.is_active = request.POST.get('is_active') == 'on'
        farmer.save()
        farmer.user.first_name = farmer.name
        farmer.user.save()
        messages.success(request, 'Farmer updated!')
        return redirect('myadmin:farmers')
    context = {'farmer': farmer}
    return render(request, 'myadmin/edit_farmer.html', context)


def view_receipt_page(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all()
    context = {'order': order, 'order_items': order_items}
    return render(request, 'myadmin/simple-view-receipt.html', context)

# Complete views for all URLs
