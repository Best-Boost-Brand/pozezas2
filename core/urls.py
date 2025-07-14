from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegistrationAPI,
    NomenklaturaListCreateAPIView, NomenklaturaRetrieveUpdateDestroyAPIView,
    ZahonListCreateAPIView, ZahonRetrieveUpdateDestroyAPIView,
    ChastynaListCreateAPIView, ChastynaRetrieveUpdateDestroyAPIView,
    ObladnannyaListCreateAPIView, ObladnannyaRetrieveUpdateDestroyAPIView,
    VyprobuvannyaListCreateAPIView, VyprobuvannyaRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    # JWT auth
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User registration
    path('api/register/', RegistrationAPI.as_view(), name='register'),

    # Nomenklatura CRUD
    path('api/nomenklatura/', NomenklaturaListCreateAPIView.as_view(), name='nomenklatura_list'),
    path('api/nomenklatura/<int:pk>/', NomenklaturaRetrieveUpdateDestroyAPIView.as_view(), name='nomenklatura_detail'),

    # Zahon CRUD
    path('api/zahony/', ZahonListCreateAPIView.as_view(), name='zahony_list'),
    path('api/zahony/<int:pk>/', ZahonRetrieveUpdateDestroyAPIView.as_view(), name='zahony_detail'),

    # Chastyna CRUD
    path('api/chastyny/', ChastynaListCreateAPIView.as_view(), name='chastyny_list'),
    path('api/chastyny/<int:pk>/', ChastynaRetrieveUpdateDestroyAPIView.as_view(), name='chastyny_detail'),

    # Obladnannya CRUD
    path('api/obladnannya/', ObladnannyaListCreateAPIView.as_view(), name='obladnannya_list'),
    path('api/obladnannya/<int:pk>/', ObladnannyaRetrieveUpdateDestroyAPIView.as_view(), name='obladnannya_detail'),

    # Vyprobuvannya CRUD
    path('api/vyprobuvannya/', VyprobuvannyaListCreateAPIView.as_view(), name='vyprobuvannya_list'),
    path('api/vyprobuvannya/<int:pk>/', VyprobuvannyaRetrieveUpdateDestroyAPIView.as_view(), name='vyprobuvannya_detail'),
]
