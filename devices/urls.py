from django.urls import path, include
from rest_framework import routers
from .api_views import AssetViewSet

router = routers.DefaultRouter()
router.register(r'assets', AssetViewSet)

urlpatterns = [
    # ...your regular views...
    path('api/', include(router.urls)),  # The API will be at /api/assets/
]
