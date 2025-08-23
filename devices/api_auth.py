# devices/api_auth.py
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from .models import APIKey

class ApiKeyOnlyAuthentication(BaseAuthentication):
    """
    Authenticate exclusively by 'Api-Key' header.
    If absent -> unauthenticated (no fallback to session).
    If present but invalid -> 401.
    """
    header_name = 'Api-Key'

    def authenticate(self, request):
        key = request.headers.get(self.header_name)
        if not key:
            return None  # no auth provided
        try:
            APIKey.objects.get(key=key, is_active=True)
        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid or unauthorized API Key.')
        # Return an AnonymousUser + the key object; permissions can key off request.auth
        return (AnonymousUser(), key)

from rest_framework.permissions import BasePermission

class RequireValidApiKey(BasePermission):
    """
    Permit only if ApiKeyOnlyAuthentication succeeded (request.auth is set).
    """
    def has_permission(self, request, view):
        return bool(request.auth)
