from datetime import timedelta
import uuid

from django.utils import timezone
from django.db.models import Q

from rest_framework import status, permissions, viewsets, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import User, UserSession, Brigade, Detachment, Equipment, Testing
from .serializers import (
    LoginSerializer, LoginResponseSerializer,
    BrigadeSerializer, DetachmentSerializer,
    EquipmentSerializer, TestingSerializer
)

# ---------- PERMISSIONS ----------
class IsReadWriteOrGod(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return getattr(user, 'mode', None) in ('RW', 'GOD')

class IsGod(permissions.BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'mode', None) == 'GOD'

# ---------- AUTH ----------
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        try:
            user = User.objects.get(username=data['username'])
        except User.DoesNotExist:
            return Response({'detail': 'Невірний логін або пароль'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(data['password']):
            return Response({'detail': 'Невірний логін або пароль'}, status=status.HTTP_400_BAD_REQUEST)

        # опційно оновлюємо бригаду
        if 'brigade' in data:
            try:
                user.brigade = Brigade.id.field.related_model.objects.get(id=data['brigade'])
            except Brigade.DoesNotExist:
                return Response({'detail': 'Невірний ID частини'}, status=status.HTTP_400_BAD_REQUEST)

        # опційно оновлюємо загони
        if 'detachments' in data:
            det_ids = data['detachments']
            dets = Detachment.objects.filter(id__in=det_ids)
            if dets.count() != len(det_ids):
                return Response({'detail': 'Невірні ID загонів'}, status=status.HTTP_400_BAD_REQUEST)
            user.detachments.set(dets)

        user.save()

        # створення сесії на 8 год
        sid = uuid.uuid4().hex
        expires = timezone.now() + timedelta(hours=8)
        UserSession.objects.create(user=user, session_id=sid, expires=expires)

        resp = LoginResponseSerializer({
            'session_id': sid,
            'mode': user.mode,
            'brigade': user.brigade.name if user.brigade else None,
            'detachments': [d.name for d in user.detachments.all()]
        })
        return Response(resp.data)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            sid = auth.split(' ')[1]
            UserSession.objects.filter(session_id=sid).delete()
        return Response(status=204)

class AdminRegistrationView(APIView):
    permission_classes = [IsGod]

    def post(self, request):
        payload = request.data
        username = payload.get('username')
        password = payload.get('password')
        mode = payload.get('mode', 'RO')
        brigade_id = payload.get('brigade')
        detachment_ids = payload.get('detachments', [])

        if mode not in {'RO','RW','GOD'}:
            return Response({'detail': 'Невірний режим'}, status=400)

        if not username or not password:
            return Response({'detail': 'Потрібні username і password'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'detail': 'Такий користувач вже існує'}, status=400)

        brigade = None
        if brigade_id:
            try:
                brigade = Brigade.objects.get(id=brigade_id)
            except Brigade.DoesNotExist:
                return Response({'detail':'Невірний ID частини'}, status=400)

        user = User.objects.create_user(username=username, password=password, mode=mode, brigade=brigade)

        if detachment_ids:
            dets = Detachment.objects.filter(id__in=detachment_ids)
            if dets.count() != len(detachment_ids):
                return Response({'detail':'Невірні ID загонів'}, status=400)
            user.detachments.set(dets)

        return Response({'id': user.id, 'username': user.username, 'mode': user.mode}, status=201)

class AdminModeChangeView(APIView):
    permission_classes = [IsGod]

    def put(self, request):
        user_id = request.data.get('user_id')
        new_mode = request.data.get('mode')
        if new_mode not in {'RO','RW','GOD'}:
            return Response({'detail':'Невірний режим'}, status=400)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail':'Користувача не знайдено'}, status=404)
        user.mode = new_mode
        user.save()
        return Response({'id': user.id, 'mode': user.mode})

# ---------- VIEWSETS ----------
class BrigadeViewSet(viewsets.ModelViewSet):
    queryset = Brigade.objects.all()
    serializer_class = BrigadeSerializer
    permission_classes = [permissions.IsAuthenticated, IsReadWriteOrGod]

class DetachmentViewSet(viewsets.ModelViewSet):
    queryset = Detachment.objects.all()
    serializer_class = DetachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsReadWriteOrGod]

class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsReadWriteOrGod]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'type': ['exact', 'icontains'],
        'brigade': ['exact'],
        'inventory_number': ['exact', 'icontains'],
    }

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.mode != 'GOD':
            qs = qs.filter(brigade=user.brigade)
        return qs

class TestingViewSet(viewsets.ModelViewSet):
    queryset = Testing.objects.all()
    serializer_class = TestingSerializer
    permission_classes = [permissions.IsAuthenticated, IsReadWriteOrGod]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'equipment__type': ['exact', 'icontains'],
        'equipment': ['exact'],
        'date': ['exact', 'gte', 'lte'],
        'next_date': ['exact', 'gte', 'lte'],
    }

    def get_queryset(self):
        user = self.request.user
        if user.mode == 'GOD':
            return Testing.objects.all()
        return Testing.objects.filter(equipment__brigade=user.brigade)

    def perform_create(self, serializer):
        serializer.save(tested_by=self.request.user)

# ---------- LIST BY TYPE: /api/testing/<etype>/ ----------
class TestingByTypeView(generics.ListAPIView):
    serializer_class = TestingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    # фільтри збережуться (можна додати ?date__gte=... тощо)
    filterset_fields = {
        'date': ['exact', 'gte', 'lte'],
        'next_date': ['exact', 'gte', 'lte'],
    }

    def get_queryset(self):
        etype = self.kwargs.get('etype')  # напр., "драбини"
        user = self.request.user
        base = Testing.objects.filter(equipment__type__iexact=etype)
        if user.mode == 'GOD':
            return base
        return base.filter(equipment__brigade=user.brigade)
