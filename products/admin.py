
from django.contrib import admin
from .models import Product, Order, OrderItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "price",
        "stock",
        "created_at",
    )

    list_display_links = ("name",)
    list_editable = ("price", "stock")
    search_fields = ("name", "description")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    list_per_page = 20


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "quantity", "price")
    autocomplete_fields = ("product",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "email",
        "total_amount",
        "status",
        "created_at",
    )

    list_display_links = ("id", "full_name")
    list_editable = ("status",)
    list_filter = ("status", "created_at")
    search_fields = (
        "full_name",
        "email",
        "phone",
        "user__username",
    )

    readonly_fields = ("created_at",)
    inlines = (OrderItemInline,)
    ordering = ("-created_at",)
    list_per_page = 20


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "product",
        "quantity",
        "price",
    )

    search_fields = (
        "product__name",
        "order__full_name",
        "order__email",
    )

    list_select_related = ("order", "product")
    list_per_page = 20
