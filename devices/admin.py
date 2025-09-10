from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    DevicesAttributes, Manufacturer, Deployment, Classification, Flexibility,
    Communication, CommunicationProtocol, Regulation,
    Units, CellType, VoltageRegulationOption, BessApplication, BESSSpecs,
    InverterSpecs, PVModuleSpecs, SCCSpecs, EnergyMeterSpecs,
    APIKey
)

# --- Existing registrations ---
admin.site.register(DevicesAttributes)
admin.site.register(Manufacturer)
admin.site.register(Deployment)
admin.site.register(Classification)
admin.site.register(Flexibility)
admin.site.register(Communication)
admin.site.register(CommunicationProtocol)
admin.site.register(Regulation)
admin.site.register(Units)
admin.site.register(CellType)
admin.site.register(InverterSpecs)
admin.site.register(PVModuleSpecs)
admin.site.register(SCCSpecs)
admin.site.register(EnergyMeterSpecs)

@admin.register(VoltageRegulationOption)
class VoltageRegulationOptionAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(BessApplication)
class BessApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_name',)
    search_fields = ('application_name',)

@admin.register(BESSSpecs)
class BESSSpecsAdmin(admin.ModelAdmin):
    list_display = ('asset', 'bess_application', 'cell_type', 'voltage_nominal')
    list_filter  = ('bess_application', 'cell_type')
    autocomplete_fields = ('bess_application',)


# --- APIKey admin (no raw secret shown) ---
@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("user", "fingerprint", "is_active", "created_at", "rotated_at", "last_used_at", "last_used_ip")
    list_filter = ("is_active",)
    search_fields = ("user__username", "key_hash")
    readonly_fields = ("key_hash", "created_at", "rotated_at", "last_used_at", "last_used_ip")


# --- Extend Users list to show API key fingerprint/status, not the raw key ---
class UserAdmin(DjangoUserAdmin):
    """
    Adds an 'API key' column to the Users changelist.
    Shows a short fingerprint + status; never reveals the raw key.
    """
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "api_key_info")

    @admin.display(description="API key")
    def api_key_info(self, obj: User):
        try:
            k = obj.api_key  # OneToOne: may raise APIKey.DoesNotExist
            if k and k.is_active:
                return f"{k.fingerprint()} (active)"
            elif k:
                return f"{k.fingerprint()} (revoked)"
        except APIKey.DoesNotExist:
            pass
        return ""


# Replace default User admin with our extended one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
