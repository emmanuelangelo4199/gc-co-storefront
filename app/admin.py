from django.contrib import admin
from .models import Cart, Order, Order_Items, Product, cart_Items, userAccount


@admin.register(Product)
class productAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_quantity', 'created_at', 'is_bestseller')
    search_fields = ('name', 'is_sale')

@admin.register(userAccount)
class user_accountAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone_number']
    search_fields = ['email']

@admin.register(Order)
class orderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status')
    search_fields = ('user', 'order_number')


@admin.register(Order_Items)
class order_itemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'unit_price')
    search_fields = ('order', 'product')


@admin.register(Cart)
class cart_Admin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    search_fields = ['user']


@admin.register(cart_Items)
class cart_itemsAdmin(admin.ModelAdmin):
    list_display = ['cart']