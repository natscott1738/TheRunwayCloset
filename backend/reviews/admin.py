from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "product",
        "rating",
        "created_at",
        "updated_at",
    )
    list_filter = ("rating", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "product__name", "comment")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")
