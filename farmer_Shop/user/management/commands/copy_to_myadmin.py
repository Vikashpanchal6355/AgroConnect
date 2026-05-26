"""
Management command to copy data from user models to myadmin models
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from user.models import (
    User as UserModel,
    Category as UserCategory,
    Product as UserProduct,
    Order as UserOrder,
    OrderItem as UserOrderItem,
    Contact_us as UserContact,
    Wishlist as UserWishlist,
    Cart as UserCart,
    CartItem as UserCartItem,
    UserAddress as UserAddress,
    SiteSettings as UserSiteSettings
)
from myadmin.models import (
    Category,
    Product,
    Order,
    OrderItem,
    Contact_us,
    Wishlist,
    Cart,
    CartItem,
    UserAddress,
    SiteSettings
)


class Command(BaseCommand):
    help = 'Copy data from user models to myadmin models'

    def handle(self, *args, **options):
        self.stdout.write('Starting data migration from user to myadmin...')
        
        # Copy SiteSettings
        self.copy_site_settings()
        
        # Copy Categories
        self.copy_categories()
        
        # Copy Products
        self.copy_products()
        
        # Copy Contact_us
        self.copy_contacts()
        
        # Copy Orders
        self.copy_orders()
        
        # Copy Wishlists
        self.copy_wishlists()
        
        # Copy Carts
        self.copy_carts()
        
        # Copy UserAddresses
        self.copy_addresses()
        
        self.stdout.write(self.style.SUCCESS('Data migration completed successfully!'))
    
    def copy_site_settings(self):
        user_settings = UserSiteSettings.objects.all()
        count = 0
        for us in user_settings:
            SiteSettings.objects.update_or_create(
                id=us.id,
                defaults={
                    'notification_banner': us.notification_banner,
                    'is_notification_active': us.is_notification_active,
                }
            )
            count += 1
        self.stdout.write(f'  Copied {count} site settings')
    
    def copy_categories(self):
        user_categories = UserCategory.objects.all()
        count = 0
        for uc in user_categories:
            Category.objects.update_or_create(
                id=uc.id,
                defaults={
                    'name': uc.name,
                    'description': uc.description,
                    'meta_title': getattr(uc, 'meta_title', ''),
                    'meta_description': getattr(uc, 'meta_description', ''),
                }
            )
            count += 1
        self.stdout.write(f'  Copied {count} categories')
    
    def copy_products(self):
        user_products = UserProduct.objects.all()
        count = 0
        for up in user_products:
            try:
                category = Category.objects.get(id=up.category_id) if up.category_id else None
            except Category.DoesNotExist:
                category = None
            
            Product.objects.update_or_create(
                id=up.id,
                defaults={
                    'name': up.name,
                    'category': category,
                    'description': up.description,
                    'additional_info': up.additional_info,
                    'reviews': up.reviews,
                    'price': up.price,
                    'original_price': up.original_price,
                    'image': up.image,
                    'rating': up.rating,
                    'is_new': up.is_new,
                    'is_hot': up.is_hot,
                    'is_sale': up.is_sale,
                    'stock': up.stock,
                    'view_count': up.view_count,
                    'sold_count': up.sold_count,
                    'sku': up.sku,
                    'tags': up.tags,
                }
            )
            count += 1
        self.stdout.write(f'  Copied {count} products')
    
    def copy_contacts(self):
        user_contacts = UserContact.objects.all()
        count = 0
        for uc in user_contacts:
            Contact_us.objects.update_or_create(
                id=uc.id,
                defaults={
                    'name': uc.name,
                    'email': uc.email,
                    'phone': uc.phone,
                    'message': uc.message,
                    'is_read': getattr(uc, 'is_read', False),
                }
            )
            count += 1
        self.stdout.write(f'  Copied {count} contact messages')
    
    def copy_orders(self):
        user_orders = UserOrder.objects.all()
        count = 0
        for uo in user_orders:
            try:
                user = User.objects.filter(id=uo.user_id).first() if uo.user_id else None
            except User.DoesNotExist:
                user = None
            
            Order.objects.update_or_create(
                id=uo.id,
                defaults={
                    'order_number': uo.order_number,
                    'user': user,
                    'session_id': uo.session_id,
                    'first_name': uo.first_name,
                    'last_name': uo.last_name,
                    'email': uo.email,
                    'phone': uo.phone,
                    'address_line_1': uo.address_line_1,
                    'address_line_2': uo.address_line_2,
                    'city': uo.city,
                    'state': uo.state,
                    'postal_code': uo.postal_code,
                    'country': uo.country,
                    'status': uo.status,
                    'subtotal': uo.subtotal,
                    'shipping_cost': uo.shipping_cost,
                    'total': uo.total,
                    'payment_method': uo.payment_method,
                    'payment_status': uo.payment_status,
                    'razorpay_payment_id': uo.razorpay_payment_id,
                    'razorpay_order_id': uo.razorpay_order_id,
                    'notes': uo.notes,
                }
            )
            count += 1
        self.stdout.write(f'  Copied {count} orders')
        
        # Copy OrderItems
        self.copy_order_items()
    
    def copy_order_items(self):
        user_order_items = UserOrderItem.objects.all()
        count = 0
        for uoi in user_order_items:
            try:
                order = Order.objects.get(id=uoi.order_id) if uoi.order_id else None
                product = Product.objects.get(id=uoi.product_id) if uoi.product_id else None
            except (Order.DoesNotExist, Product.DoesNotExist):
                continue
            
            if order and product:
                OrderItem.objects.update_or_create(
                    id=uoi.id,
                    defaults={
                        'order': order,
                        'product': product,
                        'quantity': uoi.quantity,
                        'price': uoi.price,
                        'subtotal': uoi.subtotal,
                    }
                )
                count += 1
        self.stdout.write(f'  Copied {count} order items')
    
    def copy_wishlists(self):
        user_wishlists = UserWishlist.objects.all()
        count = 0
        for uw in user_wishlists:
            try:
                user = User.objects.filter(id=uw.user_id).first() if uw.user_id else None
                product = Product.objects.get(id=uw.product_id) if uw.product_id else None
            except (User.DoesNotExist, Product.DoesNotExist):
                continue
            
            if product:
                Wishlist.objects.get_or_create(
                    id=uw.id,
                    defaults={
                        'user': user,
                        'session_id': uw.session_id,
                        'product': product,
                    }
                )
                count += 1
        self.stdout.write(f'  Copied {count} wishlists')
    
    def copy_carts(self):
        user_carts = UserCart.objects.all()
        count = 0
        for uc in user_carts:
            try:
                user = User.objects.filter(id=uc.user_id).first() if uc.user_id else None
            except User.DoesNotExist:
                user = None
            
            Cart.objects.update_or_create(
                id=uc.id,
                defaults={
                    'session_id': uc.session_id,
                    'user': user,
                }
            )
            count += 1
        self.stdout.write(f'  Copied {count} carts')
        
        # Copy CartItems
        self.copy_cart_items()
    
    def copy_cart_items(self):
        user_cart_items = UserCartItem.objects.all()
        count = 0
        for uci in user_cart_items:
            try:
                cart = Cart.objects.get(id=uci.cart_id) if uci.cart_id else None
                product = Product.objects.get(id=uci.product_id) if uci.product_id else None
            except (Cart.DoesNotExist, Product.DoesNotExist):
                continue
            
            if cart and product:
                CartItem.objects.update_or_create(
                    id=uci.id,
                    defaults={
                        'cart': cart,
                        'product': product,
                        'quantity': uci.quantity,
                    }
                )
                count += 1
        self.stdout.write(f'  Copied {count} cart items')
    
    def copy_addresses(self):
        user_addresses = UserAddress.objects.all()
        count = 0
        for ua in user_addresses:
            try:
                user = User.objects.filter(id=ua.user_id).first() if ua.user_id else None
            except User.DoesNotExist:
                user = None
            
            if user:
                UserAddress.objects.update_or_create(
                    id=ua.id,
                    defaults={
                        'user': user,
                        'first_name': ua.first_name,
                        'last_name': ua.last_name,
                        'address_line_1': ua.address_line_1,
                        'address_line_2': ua.address_line_2,
                        'city': ua.city,
                        'state': ua.state,
                        'postal_code': ua.postal_code,
                        'country': ua.country,
                        'phone': ua.phone,
                        'is_default': ua.is_default,
                    }
                )
                count += 1
        self.stdout.write(f'  Copied {count} user addresses')