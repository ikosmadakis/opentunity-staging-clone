# devices/api_kpis.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from devices.kpi import compute_kpis
from devices.api_auth import ApiKeyOnlyAuthentication, RequireValidApiKey
from devices.models import APIKey, ContentContributor

class IsEconomicOperatorOnly(IsAuthenticated):
    """
    Extra guard: ensure the API key belongs to a MANUFACTURER (EO).
    Mirrors your asset_api_key_entry role check.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        # request.auth contains the raw key from ApiKeyOnlyAuthentication
        raw = request.auth
        if not raw:
            return False
        try:
            hashed = APIKey.hash(raw)
            k = (APIKey.objects.filter(is_active=True)
                 .filter(Q(key_hash=hashed) | Q(key=raw))
                 .select_related("user")
                 .first())
            if not k or not k.user:
                return False
            cc = ContentContributor.objects.filter(user=k.user).only("role").first()
            return bool(cc and (cc.role or "").upper() == "MANUFACTURER")
        except Exception:
            return False

class KpiOverviewView(APIView):
    """
    GET /api/kpis/overview?h=48&qr_type=OT|DPP
    Auth: Api-Key header or ?apikey=
    Role: MANUFACTURER (EO) only
    Returns: global KPIs (not scoped)
    """
    authentication_classes = [ApiKeyOnlyAuthentication]
    permission_classes = [RequireValidApiKey]

    def get(self, request):
        try:
            hours = int(request.GET.get("h", 48))
        except Exception:
            hours = 48
        hours = max(1, min(hours, 720))

        qr_type = request.GET.get("qr_type")
        if qr_type not in (None, "OT", "DPP"):
            qr_type = None

        return Response(compute_kpis(hours=hours, qr_type=qr_type))
