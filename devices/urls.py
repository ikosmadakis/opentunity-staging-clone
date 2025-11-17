from django.urls import path, include
from .api_views import AssetViewSet, NoRootRouter
from devices.dpp_views import DPPResolveView, DPPImportView, DPPAssetView
from devices.eo_views import EOAssetIngestView

from . import views

router = NoRootRouter()
router.register(r'assets', AssetViewSet)

urlpatterns = [
    path('api/assets/<int:asset_id>/enter-api-key/', views.asset_api_key_entry,
         name='asset_api_key_entry'),
    path('api/', include(router.urls)),  # The API will be at /api/assets/
    path('api_qr/<int:asset_id>/', views.api_qr_view, name='api_qr'),
    path("api/dpp/resolve", DPPResolveView.as_view(), name="dpp_resolve"),
    path("api/dpp/import",  DPPImportView.as_view(),  name="dpp_import"),
    path("api/dpp/asset",   DPPAssetView.as_view(),   name="dpp_asset"),
    path("api/eo/assets/", EOAssetIngestView.as_view(), name="eo_asset_ingest"),
]
