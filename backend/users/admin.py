from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username','email','role','is_staff','is_active','date_joined')
    list_filter = ('role','is_staff','is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Runway', {'fields': ('role','phone_number')}),
    )
