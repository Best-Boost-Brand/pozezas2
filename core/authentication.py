from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.utils import timezone
from .models import UserSession

class SessionIDAuthentication(BaseAuthentication):
    """
    Читає заголовок 'session-id' і аутентифікує користувача через UserSession.
    """
    def authenticate(self, request):
        sid = request.META.get("HTTP_SESSION_ID") or request.headers.get("session-id")
        if not sid:
            return None
        try:
            s = UserSession.objects.select_related("user").get(session_id=sid)
        except UserSession.DoesNotExist:
            raise exceptions.AuthenticationFailed("Session expired")
        if not s.is_active():
            s.delete()
            raise exceptions.AuthenticationFailed("Session expired")
        return (s.user, None)
