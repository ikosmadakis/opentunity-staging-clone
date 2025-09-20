# devices/api_auth.py
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from .models import APIKey

class ApiKeyOnlyAuthentication(BaseAuthentication):
    """
    Accept API key via:
      - Header:  Api-Key: <key>   (also X-API-Key / X-Api-Key)
      - Query:   ?apikey=<key>
    Works with legacy plaintext (APIKey.key) OR hashed (APIKey.key_hash).
    """
    header_names = ("Api-Key", "X-API-Key", "X-Api-Key", "Authorization")

    def _extract_from_headers(self, request):
        for h in self.header_names:
            v = request.headers.get(h)
            if not v:
                continue
            v = v.strip()
            if not v:
                continue
            # Support "Api-Key <key>" in Authorization
            if h.lower() == "authorization":
                if v.lower().startswith("api-key "):
                    return v.split(" ", 1)[1].strip()
                # leave other auth schemes untouched
                continue
            return v
        return None

    def authenticate(self, request):
        # 1) Try headers
        key = self._extract_from_headers(request)

        # 2) Fallback to query param
        if not key:
            key = request.query_params.get("apikey")

        # No key → unauthenticated; permission will raise 401
        if not key:
            return None

        # 3) Validate against active keys: plaintext OR hashed
        try:
            hashed = APIKey.hash(key)
        except Exception:
            hashed = None

        exists = APIKey.objects.filter(is_active=True).filter(
            Q(key=key) | (Q(key_hash=hashed) if hashed else Q(pk__isnull=True))
        ).exists()

        if not exists:
            raise exceptions.AuthenticationFailed("Invalid or unauthorized API Key.")

        # DRF expects (user, auth). We keep AnonymousUser; the raw key is in request.auth
        return (AnonymousUser(), key)


from rest_framework.permissions import BasePermission

class RequireValidApiKey(BasePermission):
    def has_permission(self, request, view):
        if request.auth:
            return True
        # No key provided (in header or query) → 401
        raise exceptions.NotAuthenticated(
            'Missing API key. Provide via header "Api-Key: <key>" or "?apikey=<key>".'
        )
