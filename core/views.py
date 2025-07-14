from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import (
    Nomenklatura, Zahon, Chastyna,
    Obladnannya, Vyprobuvannya
)
from .serializers import (
    UserSerializer, NomenklaturaSerializer, ZahonSerializer,
    ChastynaSerializer, ObladnannyaSerializer, VyprobuvannyaSerializer
)

User = get_user_model()

from .models import Access

class RegistrationAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username  = request.data.get('username')
        password  = request.data.get('password')
        chast_id  = request.data.get('chastyna')
        accesses  = request.data.get('accesses', [])

        # базова валідація
        if not username or not password:
            return Response({'detail': 'Username і password обовʼязкові'}, status=400)

        # шукаємо частину (якщо передали)
        chast = None
        if chast_id:
            from .models import Chastyna
            chast = get_object_or_404(Chastyna, id=chast_id)

        # створюємо користувача
        user = User.objects.create_user(username=username, password=password, chastyna=chast)

        # створюємо доступи
        for a in accesses:
            Access.objects.create(
                user=user,
                zahon_id   = a['zahon'],
                chastyna_id= a['chastyna'],
                level      = a['level']
            )

        return Response(UserSerializer(user).data, status=201)


# Nomenklatura CRUD
class NomenklaturaListCreateAPIView(generics.ListCreateAPIView):
    queryset = Nomenklatura.objects.all()
    serializer_class = NomenklaturaSerializer
    permission_classes = [permissions.IsAuthenticated]

class NomenklaturaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Nomenklatura.objects.all()
    serializer_class = NomenklaturaSerializer
    permission_classes = [permissions.IsAuthenticated]

# Zahon CRUD
class ZahonListCreateAPIView(generics.ListCreateAPIView):
    queryset = Zahon.objects.all()
    serializer_class = ZahonSerializer
    permission_classes = [permissions.IsAuthenticated]

class ZahonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Zahon.objects.all()
    serializer_class = ZahonSerializer
    permission_classes = [permissions.IsAuthenticated]

# Chastyna CRUD
class ChastynaListCreateAPIView(generics.ListCreateAPIView):
    queryset = Chastyna.objects.all()
    serializer_class = ChastynaSerializer
    permission_classes = [permissions.IsAuthenticated]

class ChastynaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Chastyna.objects.all()
    serializer_class = ChastynaSerializer
    permission_classes = [permissions.IsAuthenticated]

# Obladnannya CRUD
class ObladnannyaListCreateAPIView(generics.ListCreateAPIView):
    queryset = Obladnannya.objects.all()
    serializer_class = ObladnannyaSerializer
    permission_classes = [permissions.IsAuthenticated]

class ObladnannyaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Obladnannya.objects.all()
    serializer_class = ObladnannyaSerializer
    permission_classes = [permissions.IsAuthenticated]

# Vyprobuvannya CRUD
class VyprobuvannyaListCreateAPIView(generics.ListCreateAPIView):
    queryset = Vyprobuvannya.objects.all()
    serializer_class = VyprobuvannyaSerializer
    permission_classes = [permissions.IsAuthenticated]

class VyprobuvannyaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vyprobuvannya.objects.all()
    serializer_class = VyprobuvannyaSerializer
    permission_classes = [permissions.IsAuthenticated]
