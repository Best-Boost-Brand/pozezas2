from rest_framework import status, permissions, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
import uuid
from django_filters.rest_framework import DjangoFilterBackend

from .models import User, UserSession, Brigade, Detachment, Equipment, Testing
from .serializers import (
    LoginSerializer, LoginResponseSerializer,
    BrigadeSerializer, DetachmentSerializer,
    EquipmentSerializer, TestingSerializer
)

# --- PERMISSIONS ---

class IsGod(permissions.BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'mode', None) == 'GOD'

# --- LOGIN ---

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Authenticate user
        user = User.objects.filter(username=data['username']).first()
        if not user or not user.check_password(data['password']):
            return Response({'detail': 'Невірні облікові дані'}, status=status.HTTP_401_UNAUTHORIZED)

        # Update brigade if provided
        if 'brigade' in data:
            try:
                b = Brigade.objects.get(id=data['brigade'])
                user.brigade = b
            except Brigade.DoesNotExist:
                return Response({'detail': 'Невірний ID частини'}, status=status.HTTP_400_BAD_REQUEST)

        # Update detachments if provided
        if 'detachments' in data:
            det_ids = data['detachments']
            dets = Detachment.objects.filter(id__in=det_ids)
            if dets.count() != len(det_ids):
                return Response({'detail': 'Невірні ID загонів'}, status=status.HTTP_400_BAD_REQUEST)
            user.detachments.set(dets)

        user.save()

        # Create session
        sid = uuid.uuid4().hex
        expires = timezone.now() + timedelta(hours=8)
        UserSession.objects.create(user=user, session_id=sid, expires=expires)

        resp = {
            'session_id': sid,
            'mode': user.mode,
            'brigade': user.brigade.name if user.brigade else None,
            'detachments': [d.name for d in user.detachments.all()]
        }
        return Response(resp)

# --- SUPERUSER: CREATE USER ---

class AdminRegistrationView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsGod]

    def post(self, request):
        data = request.data
        if data.get('password') != data.get('confirmPassword'):
            return Response({'detail': 'Паролі не співпадають'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=data['username']).exists():
            return Response({'detail': 'Такий користувач вже існує'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            b = Brigade.objects.get(id=data['brigade'])
        except Brigade.DoesNotExist:
            return Response({'detail': 'Невірний ID частини'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            brigade=b,
            mode=data.get('mode', 'RO')  # default RO
        )

        if 'detachments' in data:
            det_ids = data['detachments']
            dets = Detachment.objects.filter(id__in=det_ids)
            if dets.count() != len(det_ids):
                return Response({'detail': 'Невірні ID загонів'}, status=status.HTTP_400_BAD_REQUEST)
            user.detachments.set(dets)

        user.save()
        return Response({'id': user.id}, status=status.HTTP_201_CREATED)

# --- SUPERUSER: CHANGE MODE ---

class AdminModeChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsGod]

    def put(self, request):
        try:
            user = User.objects.get(id=request.data['userId'])
        except User.DoesNotExist:
            return Response({'detail': 'Користувач не знайдений'}, status=status.HTTP_404_NOT_FOUND)

        user.mode = request.data.get('mode', user.mode)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

# --- CRUD BRIGADE ---

class BrigadeViewSet(viewsets.ModelViewSet):
    queryset = Brigade.objects.all()
    serializer_class = BrigadeSerializer
    permission_classes = [permissions.IsAuthenticated, IsGod]

# --- CRUD DETACHMENT ---

class DetachmentViewSet(viewsets.ModelViewSet):
    queryset = Detachment.objects.all()
    serializer_class = DetachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsGod]

# --- CRUD EQUIPMENT (доступно всім увійшовшим) ---

class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [permissions.IsAuthenticated]

# --- CRUD TESTING (з фільтром по brigade для не-GOD) ---

class TestingViewSet(viewsets.ModelViewSet):
    queryset = Testing.objects.all()
    serializer_class = TestingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'equipment__type': ['exact', 'icontains'],
        'equipment': ['exact'],  # додатково, для точного фільтрування
    }

    def get_queryset(self):
        user = self.request.user
        if user.mode == 'GOD':
            return Testing.objects.all()
        return Testing.objects.filter(equipment__brigade=user.brigade)

    def perform_create(self, serializer):
        serializer.save(tested_by=self.request.user)

