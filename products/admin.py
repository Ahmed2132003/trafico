from django.contrib import admin
from django.conf import settings
from .models import Product, Favorite, CartItem, Order, OrderItem, Governorate , ProductSize , ProductColor

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'stock', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    search_fields = ('user__username', 'product__name')
    list_filter = ('added_at',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'marketer_commission')
    search_fields = ('user__username', 'product__name')
    list_filter = ('user',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'customer_name', 'total_price', 'status', 'created_at')
    search_fields = ('user__username', 'customer_name')
    list_filter = ('status', 'created_at')
    list_editable = ('status',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'marketer_commission')
    search_fields = ('order__id', 'product__name')
    list_filter = ('order',)

@admin.register(Governorate)
class GovernorateAdmin(admin.ModelAdmin):
    list_display = ('name', 'shipping_cost')
    search_fields = ('name',)
    
admin.site.register(ProductSize)
admin.site.register(ProductColor)