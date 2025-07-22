from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView, AdminRegistrationView, AdminModeChangeView,
    BrigadeViewSet, DetachmentViewSet, EquipmentViewSet, TestingViewSet
)

router = DefaultRouter()
router.register(r'brigade', BrigadeViewSet)
router.register(r'detachment', DetachmentViewSet)
router.register(r'equipment', EquipmentViewSet)
router.register(r'testing', TestingViewSet, basename='testing')  # specify basename explicitly

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('admin/registration/', AdminRegistrationView.as_view(), name='admin-registration'),
    path('admin/mode/', AdminModeChangeView.as_view(), name='admin-mode'),
    path('', include(router.urls)),
]