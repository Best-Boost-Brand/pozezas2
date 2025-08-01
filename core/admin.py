from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Brigade, Detachment, UserSession

admin.site.register(Brigade)
admin.site.register(Detachment)
admin.site.register(UserSession)

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Додатково', {'fields': ('mode', 'brigade', 'detachments')}),
    )

admin.site.register(User, UserAdmin)
