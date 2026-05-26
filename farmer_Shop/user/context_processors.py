from django.db.models import Count
from django.utils.translation import get_language
from .models import Cart, Category, SiteSettings

def cart_context(request):
    cart = None
    cart_count = 0
    cart_total = 0
    
    if request.session.session_key:
        # Only get existing cart, don't create new one automatically
        cart = Cart.objects.filter(session_id=request.session.session_key).first()
        if cart and cart.items.exists():
            # Only calculate if cart has items
            cart_count = sum(item.quantity for item in cart.items.all())
            cart_total = sum(item.subtotal for item in cart.items.all())
    
    return {
        'cart': cart,
        'cart_count': cart_count,
        'cart_total': cart_total,
    }

def categories_context(request):
    categories = Category.objects.annotate(product_count=Count('product'))
    return {
        'categories': categories,
    }

def language_context(request):
    """Add current language to context"""
    return {
        'current_language': get_language() or 'en',
    }

def notification_context(request):
    """Add notification banner settings to context"""
    settings = SiteSettings.get_settings()
    return {
        'notification_banner': settings.notification_banner if settings.is_notification_active else '',
        'is_notification_active': settings.is_notification_active,
    }
