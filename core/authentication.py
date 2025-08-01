# authentication.py
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import UserSession

class SessionIDAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        session_id = auth_header.split(' ')[1]

        try:
            session = UserSession.objects.get(session_id=session_id)
        except UserSession.DoesNotExist:
            raise AuthenticationFailed('Invalid session ID')

        if session.expires < timezone.now():
            raise AuthenticationFailed('Session expired')

        return (session.user, None)
