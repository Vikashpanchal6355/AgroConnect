from django.contrib import admin
from .models import Farmer, Category, Product, Contact_us, Cart, CartItem, Order, OrderItem, UserAddress, Wishlist, SiteSettings

@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'user__username', 'phone')
    readonly_fields = ('created_at',)

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Contact_us)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(UserAddress)
admin.site.register(Wishlist)
admin.site.register(SiteSettings)
