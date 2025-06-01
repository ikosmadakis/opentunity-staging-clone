from django.urls import path, include
from rest_framework import routers
from .api_views import AssetViewSet, NoRootRouter
from . import views

router = NoRootRouter()
router.register(r'assets', AssetViewSet)

urlpatterns = [
    # ...your regular views...
    path('api/', include(router.urls)),  # The API will be at /api/assets/
    path('api_qr/<int:asset_id>/', views.api_qr_view, name='api_qr'),
]
