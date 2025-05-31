from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from .models import Asset
from .serializers import AssetSerializer
from rest_framework.routers import DefaultRouter


class AssetViewSet(viewsets.ReadOnlyModelViewSet):  # Only GET is allowed
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

    def list(self, request, *args, **kwargs):
        # You can return 404 or 403 or a custom message
        raise NotFound(detail="Listing all assets is not allowed.")

        # Alternatively, for a different status:
        # return Response({'detail': '-- Listing all assets is not allowed.'}, status=status.HTTP_403_FORBIDDEN)


class NoRootRouter(DefaultRouter):
    def get_api_root_view(self, api_urls=None):
        # Return a view that always raises 404
        from rest_framework.views import APIView
        from rest_framework.exceptions import NotFound

        class RootView(APIView):
            def get(self, request, *args, **kwargs):
                raise NotFound()
        return RootView.as_view()
