from django.contrib import admin
from .models import Product


@admin.register(Product)
class productAdmin(admin.ModelAdmin):
    list_display = ('name', 'inventory', 'created_at')
    search_fields = ('name', 'is_sale')