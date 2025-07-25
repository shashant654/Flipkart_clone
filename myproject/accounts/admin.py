from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Unregister the default User model if it's registered (only needed if you've replaced AUTH_USER_MODEL)
# admin.site.unregister(User)

# Register your CustomUser with a custom UserAdmin
class CustomUserAdmin(UserAdmin):
    # Add the new fields to both fieldsets and add_fieldsets
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'mobile_number', 'alternate_number', 'gender', 'dob', 'city', 'state', 'country', 'profile_picture')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'mobile_number'),
        }),
    )
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'mobile_number', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'mobile_number')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

# Register your models here
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ContactMessage)
admin.site.register(Wishlist)