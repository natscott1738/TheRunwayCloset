from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "status",
        "method",
        "amount",
        "currency",
        "provider_ref",
        "raw",
        "phone",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "currency", "method", "created_at")
    search_fields = ("order__id", "provider_ref", "raw", "phone", "id")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
    
    # Optional: allow quick change of status from list view
    list_editable = ("status",)

    def method(self, obj):
        """
        Return the payment method inferred from provider_ref or other internal logic.
        For now, we can store a 'method' field in Payment if needed.
        """
        if obj.provider_ref and obj.provider_ref.startswith("RUNWAY-"):
            return "bank_transfer"
        return "mpesa"
    method.short_description = "Payment Method"
