# devices/auth.py
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone

from .models import APIKey

def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

class APIKeyAuthentication(BaseAuthentication):
    """
    Accept any of:
      - Authorization: Api-Key <rawkey>
      - X-API-Key: <rawkey>
      - ?apikey=<rawkey>   (compatibility)
    Matches against SHA-256 hash stored in APIKey.key_hash.
    """
    def authenticate(self, request):
        raw = None

        # Authorization: Api-Key <raw>
        auth = get_authorization_header(request).decode("utf-8") if get_authorization_header(request) else ""
        if auth.startswith("Api-Key "):
            raw = auth.split(" ", 1)[1].strip()

        # X-API-Key header
        if not raw:
            raw = request.headers.get("X-API-Key")

        # ?apikey= compatibility (both DRF and plain Django)
        if not raw:
            raw = getattr(getattr(request, "query_params", None), "get", lambda *_: None)("apikey")
        if not raw:
            raw = request.GET.get("apikey") if hasattr(request, "GET") else None

        if not raw:
            return None  # let other auth backends try

        try:
            ak = APIKey.objects.get(key_hash=APIKey.hash(raw), is_active=True)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid or unauthorized API Key.")

        # audit
        APIKey.objects.filter(pk=ak.pk).update(last_used_at=timezone.now(), last_used_ip=_client_ip(request))
        return (ak.user, None)