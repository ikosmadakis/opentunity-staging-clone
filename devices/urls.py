from django.urls import path, include
from .api_views import AssetViewSet, NoRootRouter
from . import views

router = NoRootRouter()
router.register(r'assets', AssetViewSet)

urlpatterns = [
    path('api/assets/<int:asset_id>/enter-api-key/', views.asset_api_key_entry,
         name='asset_api_key_entry'),
    path('api/', include(router.urls)),  # The API will be at /api/assets/
    path('api_qr/<int:asset_id>/', views.api_qr_view, name='api_qr'),
]
