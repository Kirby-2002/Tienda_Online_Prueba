from django.contrib import admin
from .models import Category, Product, ProductImage, Supply, Order, OrderImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "featured", "created")
    list_filter = ("category", "featured")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "quantity", "unit", "brand", "color")
    list_filter = ("type", "brand", "color")
    search_fields = ("name", "type", "brand")


class OrderImageInline(admin.TabularInline):
    model = OrderImage
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "platform", "status", "payment_status", "created")
    list_filter = ("platform", "status", "payment_status")
    search_fields = ("customer_name", "email", "phone")
    readonly_fields = ("token", "created")
    inlines = [OrderImageInline]

