from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView, LogoutView, AdminRegistrationView, AdminModeChangeView,
    BrigadeViewSet, DetachmentViewSet, EquipmentViewSet, TestingViewSet,
    TestingByTypeView,
)

router = DefaultRouter()
router.register(r'brigades', BrigadeViewSet)
router.register(r'detachments', DetachmentViewSet)
router.register(r'equipment', EquipmentViewSet)
router.register(r'testing', TestingViewSet)

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('admin/registration/', AdminRegistrationView.as_view()),
    path('admin/mode/', AdminModeChangeView.as_view()),

    # список випробувань конкретного типу (наприклад, /api/testing/драбини/)
    path('testing/<str:etype>/', TestingByTypeView.as_view()),

    path('', include(router.urls)),
]
