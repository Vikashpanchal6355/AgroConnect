from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from .models import Contact_us, Category, Product, Cart, CartItem, Order, OrderItem, UserAddress, Wishlist, SiteSettings

# Register your models here.

admin.site.register(Contact_us)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('session_id', 'user__username')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_new', 'is_hot', 'is_sale', 'rating', 'stock', 'view_count', 'sold_count')
    list_filter = ('category', 'is_new', 'is_hot', 'is_sale', 'created_at')
    search_fields = ('name', 'category__name', 'sku', 'tags')
    readonly_fields = ('created_at',)
    # Using flat layout instead of fieldsets for better Jazzmin compatibility
    fields = ['name', 'category', 'description', 'price', 'original_price', 'image', 'rating', 'stock', 'view_count', 'sold_count', 'additional_info', 'reviews', 'sku', 'tags', 'is_new', 'is_hot', 'is_sale']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'first_name', 'last_name', 'email', 'total', 'status', 'payment_status', 'created_at', 'print_receipt_button')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    actions = ['print_selected_receipts']
    
    def print_receipt_button(self, obj):
        return format_html(
            '<a class="button" href="/print-receipt/{}/" target="_blank" style="padding: 5px 10px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 3px;">Print Receipt</a>',
            obj.id
        )
    print_receipt_button.short_description = 'Print Receipt'
    
    def print_selected_receipts(self, request, queryset):
        if queryset.count() == 1:
            order = queryset.first()
            return HttpResponseRedirect(f'/print-receipt/{order.id}/')
        else:
            self.message_user(request, 'Please select only one order to print a receipt.', level='ERROR')
    print_selected_receipts.short_description = 'Print Receipt for Selected Orders'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'subtotal')
    search_fields = ('order__order_number', 'product__name')


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('notification_banner', 'is_notification_active')
    fieldsets = (
        ('Notification Banner', {
            'fields': ('notification_banner', 'is_notification_active')
        }),
    )
