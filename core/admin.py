from django.contrib import admin
from .models import Brigade, Detachment, User, UserSession, Nomenclature, Equipment, Testing
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

@admin.register(Brigade)
class BrigadeAdmin(admin.ModelAdmin):
    list_display = ("id","name")
    search_fields = ("name",)

@admin.register(Detachment)
class DetachmentAdmin(admin.ModelAdmin):
    list_display = ("id","name")
    search_fields = ("name",)

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Domain", {"fields": ("mode","brigade","detachments")}),
    )
    list_display = ("id","username","mode","brigade")
    list_filter = ("mode","brigade")

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("id","user","session_id","expires_at")
    search_fields = ("session_id","user__username")

@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    list_display = ("id","name","category","slug","unit","active")
    list_filter = ("category","active")
    search_fields = ("name","slug")

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("id","inventory_number","name","type","brigade","nomenclature","detachment")
    list_filter = ("brigade","type","nomenclature__category")
    search_fields = ("inventory_number","name")

@admin.register(Testing)
class TestingAdmin(admin.ModelAdmin):
    list_display = ("id","equipment","date","result","next_date")
    list_filter = ("result","date")
