# devices/api_auth.py
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth.models import AnonymousUser
from .models import APIKey

class ApiKeyOnlyAuthentication(BaseAuthentication):
    """
    Accept API key via:
      - Header:  Api-Key: <key>
      - Query:   ?apikey=<key>
    """
    header_names = ("Api-Key", "X-API-Key", "X-Api-Key")

    def authenticate(self, request):
        # 1) Try headers
        key = None
        for h in self.header_names:
            v = request.headers.get(h)
            if v:
                key = v.strip()
                break

        # 2) Fallback to query param
        if not key:
            key = request.query_params.get("apikey")

        # No key provided → unauthenticated; permission will raise 401
        if not key:
            return None

        # Column-safe lookup: key + is_active only
        if not APIKey.objects.filter(key=key, is_active=True).exists():
            raise exceptions.AuthenticationFailed("Invalid or unauthorized API Key.")

        # DRF expects (user, auth); we don't tie to a user for this scheme
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
