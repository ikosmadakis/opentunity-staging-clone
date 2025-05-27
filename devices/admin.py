from django.contrib import admin
from .models import (
    DevicesAttributes, Manufacturer, Deployment, Classification, Flexibility,
    Communication, CommunicationProtocol, Regulation,
    Units, CellType
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
