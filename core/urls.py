from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    LoginView, LogoutView,
    RegistrationView, BrigadeAdminView, DetachmentAdminView,
    NomenclatureListCreate, NomenclatureCategories,
    EquipmentViewSet, BrigadeEquipmentCreate, BrigadeEquipmentList,
    EquipmentTypesPseudoView, JavaTestingEquipmentView, TestingByTypeTextView,
    TestingViewSet,
)

router = DefaultRouter()
router.register(r'equipment', EquipmentViewSet, basename='equipment')
router.register(r'testing', TestingViewSet, basename='testing')

urlpatterns = [
    path('login', LoginView.as_view()),
    path('logout', LogoutView.as_view()),

    # admin
    path('admin/registration', RegistrationView.as_view()),
    path('admin/brigade', BrigadeAdminView.as_view()),
    path('admin/detachment', DetachmentAdminView.as_view()),

    # nomenclature
    path('nomenclature', NomenclatureListCreate.as_view()),
    path('nomenclature/categories', NomenclatureCategories.as_view()),

    # brigade equipment via nomenclature
    path('brigade/<int:brigade_id>/equipment', BrigadeEquipmentCreate.as_view()),
    path('brigade/<int:brigade_id>/equipment/list', BrigadeEquipmentList.as_view()),

    # java-style testing
    path('testing/equipments', EquipmentTypesPseudoView.as_view()),
    path('testing/brigade/<int:brigade_id>/equipment/<int:equip_type_id>', JavaTestingEquipmentView.as_view()),

    # text tabs
    path('testing/<str:type_text>/', TestingByTypeTextView.as_view()),
]

urlpatterns += router.urls
