from django.contrib import admin
from .models import (
    DevicesAttributes, Manufacturer, Deployment, Classification, Flexibility,
    Communication, CommunicationProtocol, Regulation, APIKey,
    Units, CellType, VoltageRegulationOption, BessApplication, BESSSpecs
)

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

admin.site.register(APIKey)