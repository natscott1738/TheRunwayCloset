from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user','type','title','channel','delivered','is_read','created_at')
    list_filter = ('type','channel','delivered','is_read')
    search_fields = ('title','body')
