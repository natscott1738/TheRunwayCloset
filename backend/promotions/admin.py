from django.contrib import admin
from .models import Coupon, Promotion


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_percent",
        "is_active_display",
        "start_date",
        "end_date",
        "created_at",
        "updated_at",
    )
    search_fields = ("code",)
    readonly_fields = ("id", "created_at", "updated_at", "is_active_display")
    ordering = ("-created_at",)

    def is_active_display(self, obj):
        """Return the computed is_active property (display-only)."""
        return obj.is_active
    is_active_display.boolean = True
    is_active_display.short_description = "Is active"


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "discount_percent",
        "is_active_display",
        "start_date",
        "end_date",
        "created_at",
        "updated_at",
    )
    search_fields = ("name",)
    readonly_fields = ("id", "created_at", "updated_at", "is_active_display")
    filter_horizontal = ("products",)
    ordering = ("-created_at",)

    def is_active_display(self, obj):
        """Return the computed is_active property (display-only)."""
        return obj.is_active
    is_active_display.boolean = True
    is_active_display.short_description = "Is active"
