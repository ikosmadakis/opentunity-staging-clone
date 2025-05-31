from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import APIKey
from django.contrib.auth.models import AnonymousUser

class APIKeyUser(AnonymousUser):
    @property
    def is_authenticated(self):
        return True

# In devices/authentication.py
class APIKeyAuthentication(BaseAuthentication):
    keyword = 'Api-Key'

    def authenticate(self, request):
        api_key = request.headers.get(self.keyword)
        if not api_key:
            return None
        try:
            key_obj = APIKey.objects.get(key=api_key, is_active=True)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed('Invalid or inactive API Key')

        # Return a dummy user, or None; IsAuthenticated checks for non-anonymous
        return (APIKeyUser(), key_obj)  # or return (None, key_obj)

