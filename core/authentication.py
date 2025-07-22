from rest_framework import authentication, exceptions
from django.utils import timezone
from .models import UserSession

class SessionAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        sid = request.headers.get('session-id')
        if not sid:
            return None
        try:
            sess = UserSession.objects.get(session_id=sid, expires__gt=timezone.now())
            return (sess.user, None)
        except UserSession.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid or expired session')