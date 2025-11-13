import uuid
import hashlib
from datetime import timedelta, datetime

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import SessionIDAuthentication
from .models import (
    Brigade, Detachment, User, UserSession, Nomenclature, Equipment, Testing
)
from .serializers import (
    # auth
    LoginSerializer, SessionOutSerializer,
    # admin
    BrigadeSerializer, DetachmentSerializer, UserRegistrationSerializer,
    # nomenclature
    NomenclatureOutSerializer, NomenclatureCategoryOutSerializer, NomenclatureCreateSerializer,
    # equipment
    EquipmentSerializer, BrigadeEquipmentCreateSerializer,
    # testing
    TestingSerializer, JavaTestingInSerializer, JavaTestingOutSerializer,
    JavaTestingListOutSerializer, JavaEquipmentTypeOutSerializer
)

# --- Permissions -------------------------------------------------------------

# permissions
class IsGod(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            (request.user.is_superuser or request.user.mode == "GOD")
        )

class IsRWOrGod(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            (request.user.is_superuser or request.user.mode in ("RW","GOD"))
        )

# --- Auth -------------------------------------------------------------------

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        username = ser.validated_data["username"]
        password = ser.validated_data["password"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail":"Invalid credentials"}, status=400)
        if not user.check_password(password):
            return Response({"detail":"Invalid credentials"}, status=400)

        sid = uuid.uuid4().hex
        ttl_hours = 8
        UserSession.objects.create(
            user=user,
            session_id=sid,
            expires_at=timezone.now() + timedelta(hours=ttl_hours)
        )

        payload = {
            "sessionId": sid,
            "brigadeId": user.brigade_id,
            "detachments": list(user.detachments.values_list("id", flat=True)),
        }

        # Якщо адмін (суперкористувач або GOD-режим) —
        # віддаємо структуру бригад і загонів
        if user.is_superuser or user.mode == User.MODE_GOD:
            payload["isAdmin"] = True

            brigades = Brigade.objects.all().order_by("id")
            brigades_data = []

            for b in brigades:
                # Загони, які мають хоч якесь спорядження у цій бригаді
                dets_qs = Detachment.objects.filter(
                    equipments__brigade=b
                ).distinct().order_by("id")

                brigades_data.append({
                    "id": b.id,
                    "name": b.name,
                    "detachments": DetachmentSerializer(dets_qs, many=True).data,
                })

            payload["brigades"] = brigades_data

            # Загони, які взагалі ні до якої бригади не "підв’язані" через Equipment
            unassigned_qs = Detachment.objects.filter(
                equipments__isnull=True
            ).distinct().order_by("id")
            if unassigned_qs.exists():
                payload["unassignedDetachments"] = DetachmentSerializer(
                    unassigned_qs, many=True
                ).data

        return Response(payload)


class LogoutView(APIView):
    authentication_classes = [SessionIDAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        sid = request.META.get("HTTP_SESSION_ID") or request.headers.get("session-id")
        if sid:
            UserSession.objects.filter(session_id=sid).delete()
        return Response({"ok": True})


# --- Admin minimal -----------------------------------------------------------

class RegistrationView(APIView):
    authentication_classes = [SessionIDAuthentication]
    permission_classes = [IsGod]

    def post(self, request):
        ser = UserRegistrationSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        if User.objects.filter(username=d["username"]).exists():
            return Response({"message":"username exists"}, status=400)
        user = User(username=d["username"], mode=d["mode"])
        user.set_password(d["password"])
        if d.get("brigade"):
            user.brigade_id = d["brigade"]
        user.save()
        if d.get("detachments"):
            user.detachments.set(d["detachments"])
        return Response({"id": user.id}, status=201)


class BrigadeAdminView(APIView):
    authentication_classes = [SessionIDAuthentication]
    permission_classes = [IsGod]

    def get(self, request):

        bid = request.query_params.get("id")
        if bid:
            obj = get_object_or_404(Brigade, id=bid)
            return Response(BrigadeSerializer(obj).data)
        qs = Brigade.objects.all().order_by("id")
        return Response(BrigadeSerializer(qs, many=True).data)

    def post(self, request):
        s = BrigadeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        obj = Brigade.objects.create(**s.validated_data)
        return Response(BrigadeSerializer(obj).data, status=201)

    def put(self, request):
        s = BrigadeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        obj = get_object_or_404(Brigade, id=s.validated_data["id"])
        obj.name = s.validated_data["name"]
        obj.save()
        return Response(BrigadeSerializer(obj).data)


class DetachmentAdminView(APIView):
    authentication_classes = [SessionIDAuthentication]
    permission_classes = [IsGod]

    def get(self, request):

        did = request.query_params.get("id")
        if did:
            obj = get_object_or_404(Detachment, id=did)
            return Response(DetachmentSerializer(obj).data)
        qs = Detachment.objects.all().order_by("id")
        return Response(DetachmentSerializer(qs, many=True).data)

    def post(self, request):
        s = DetachmentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        obj = Detachment.objects.create(**s.validated_data)
        return Response(DetachmentSerializer(obj).data, status=201)

    def put(self, request):
        s = DetachmentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        obj = get_object_or_404(Detachment, id=s.validated_data["id"])
        obj.name = s.validated_data["name"]
        obj.save()
        return Response(DetachmentSerializer(obj).data)

# --- Nomenclature ------------------------------------------------------------

class NomenclatureListCreate(APIView):
    authentication_classes = [SessionIDAuthentication]
    permission_classes = [IsRWOrGod]

    def get(self, request):
        category = request.query_params.get("category")
        qs = Nomenclature.objects.filter(active=True)
        if category:
            qs = qs.filter(category=category)
        return Response(NomenclatureOutSerializer(qs, many=True).data)

    def post(self, request):
        # тільки name є обов’язковим
        ser = NomenclatureCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = ser.save()
        return Response(NomenclatureOutSerializer(obj).data, status=201)


class NomenclatureCategories(APIView):
    authentication_classes = [SessionIDAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cats = Nomenclature.objects.filter(active=True).values_list("category", flat=True).distinct()
        payload = [{"code": c, "slug": c, "name": c} for c in cats]
        return Response(NomenclatureCategoryOutSerializer(payload, many=True).data)


# --- Equipment CRUD ----------------------------------------------

class EquipmentViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionIDAuthentication]
    permission_classes = [IsRWOrGod]
    serializer_class = EquipmentSerializer
    queryset = Equipment.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        brigade = self.request.query_params.get("brigade")
        inv = self.request.query_params.get("inventory_number")
        if brigade:
            qs = qs.filter(brigade_id=brigade)
        if inv:
            qs = qs.filter(inventory_number=inv)
        return qs


# Створення через бригаду + номенклатуру
class BrigadeEquipmentCreate(APIView):
    authentication_classes = [SessionIDAuthentication]
    permission_classes = [IsRWOrGod]

    def post(self, request, brigade_id: int):
        ser = BrigadeEquipmentCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        n = d["_nomenclature"]       # покладено серіалайзером
        det_id = d.get("detachment")
        eq = Equipment.objects.create(
            brigade_id=brigade_id,
            inventory_number=d["inventory_number"],
            name=n.name,
            type=n.category,  # legacy
            nomenclature=n,
            description=d.get("description",""),
            detachment_id=det_id
        )
        return Response(EquipmentSerializer(eq).data, status=201)



class BrigadeEquipmentList(APIView):
    authentication_classes = [SessionIDAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, brigade_id: int):
        category_id = request.query_params.get("category_id")
        category = request.query_params.get("category")
        qs = Equipment.objects.filter(brigade_id=brigade_id)


        if category_id:
            qs = qs.filter(nomenclature_id=category_id)
        elif category:

            qs = qs.filter(Q(type=category) | Q(nomenclature__category=category))

        return Response(EquipmentSerializer(qs, many=True).data)



def stable_id(name: str) -> int:
    # детермінований позитивний int з назви (стабільний id для типу)
    h = hashlib.md5(name.encode("utf-8")).hexdigest()[:8]
    return int(h, 16)


def build_type_map(brigade_id: int):
    # Категорії з номенклатури + запасний варіант з текстового поля type
    names = set(
        Equipment.objects.filter(brigade_id=brigade_id, nomenclature__isnull=False)
        .values_list("nomenclature__category", flat=True)
    )
    names |= set(Equipment.objects.filter(brigade_id=brigade_id).values_list("type", flat=True))
    names = {n for n in names if n}
    mapping = {stable_id(n): n for n in sorted(names)}
    return mapping


class EquipmentTypesPseudoView(APIView):
    authentication_classes = [SessionIDAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        names = set(Nomenclature.objects.filter(active=True).values_list("category", flat=True))
        names |= set(Equipment.objects.values_list("type", flat=True))
        names = {n for n in names if n}
        data = [{"id": stable_id(n), "name": n, "slug": ""} for n in sorted(names)]
        ser = JavaEquipmentTypeOutSerializer(data, many=True)
        return Response(ser.data)


class JavaTestingEquipmentView(APIView):
    authentication_classes = [SessionIDAuthentication]
    permission_classes = [IsRWOrGod]

    def get(self, request, brigade_id: int, equip_type_id: int):
        type_map = build_type_map(brigade_id)
        if equip_type_id not in type_map:
            return Response({"message":"equipment type not found"}, status=404)
        type_name = type_map[equip_type_id]
        qs = Testing.objects.filter(
            equipment__brigade_id=brigade_id
        ).filter(
            Q(equipment__nomenclature__category=type_name) | Q(equipment__type=type_name)
        ).select_related("equipment")
        items = []
        for t in qs:
            items.append({
                "testingId": t.id,
                "deviceInventoryNumber": t.equipment.inventory_number,
                "testingDate": int(datetime.combine(t.date, datetime.min.time()).timestamp()*1000),
                "testingResult": t.result,
                "nextTestingDate": int(datetime.combine(t.next_date, datetime.min.time()).timestamp()*1000) if t.next_date else None,
                "url": t.external_url or "",
            })
        return Response(JavaTestingListOutSerializer({"testingItems": items}).data)

    def post(self, request, brigade_id: int, equip_type_id: int):
        type_map = build_type_map(brigade_id)
        if equip_type_id not in type_map:
            return Response({"message":"equipment type not found"}, status=404)
        type_name = type_map[equip_type_id]
        ser = JavaTestingInSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        inv = request.data.get("deviceInventoryNumber")
        eq = Equipment.objects.filter(
            brigade_id=brigade_id,
            inventory_number=inv
        ).filter(
            Q(nomenclature__category=type_name) | Q(type=type_name)
        ).first()
        if not eq:
            return Response({"message":"equipment not found for brigade/type/inventory"}, status=400)

        t = Testing.objects.create(
            equipment=eq,
            date=d["date"],
            result=d["result"],
            next_date=d.get("next_date"),
            external_url=d.get("external_url"),
        )
        out = {
            "testingId": t.id,
            "deviceInventoryNumber": eq.inventory_number,
            "testingDate": int(datetime.combine(t.date, datetime.min.time()).timestamp()*1000),
            "testingResult": t.result,
            "nextTestingDate": int(datetime.combine(t.next_date, datetime.min.time()).timestamp()*1000) if t.next_date else None,
            "url": t.external_url or "",
        }
        return Response(out, status=201)

    def put(self, request, brigade_id: int, equip_type_id: int):
        type_map = build_type_map(brigade_id)
        if equip_type_id not in type_map:
            return Response({"message":"equipment type not found"}, status=404)
        ser = JavaTestingInSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        testing_id = request.data.get("testingId")
        if not testing_id:
            return Response({"message":"testingId required"}, status=400)
        t = get_object_or_404(Testing, id=testing_id)
        inv = request.data.get("deviceInventoryNumber")
        if t.equipment.brigade_id != brigade_id or t.equipment.inventory_number != inv:
            return Response({"message":"testing belongs to another equipment/brigade"}, status=400)
        t.date = d["date"]
        t.result = d["result"]
        t.next_date = d.get("next_date")
        t.external_url = d.get("external_url")
        t.save()
        out = {
            "testingId": t.id,
            "deviceInventoryNumber": t.equipment.inventory_number,
            "testingDate": int(datetime.combine(t.date, datetime.min.time()).timestamp()*1000),
            "testingResult": t.result,
            "nextTestingDate": int(datetime.combine(t.next_date, datetime.min.time()).timestamp()*1000) if t.next_date else None,
            "url": t.external_url or "",
        }
        return Response(out)


# Текстові ендпоінти для вкладок: /testing/мотуз/ тощо
class TestingByTypeTextView(APIView):
    authentication_classes = [SessionIDAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, type_text: str):
        brigade_id = request.user.brigade_id
        qs = Testing.objects.filter(equipment__brigade_id=brigade_id).select_related("equipment")
        tt = type_text.lower()
        filtered = qs.filter(
            Q(equipment__type__icontains=tt) |
            Q(equipment__nomenclature__category__icontains=tt)
        )
        items = []
        for t in filtered:
            items.append({
                "inventory_number": t.equipment.inventory_number,
                "date": t.date.strftime("%d.%m.%Y"),
                "result": t.result,
                "next_date": t.next_date.strftime("%d.%m.%Y") if t.next_date else None,
                "external_url": t.external_url or "",
                "id": t.id,
            })
        return Response(items)



class TestingViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionIDAuthentication]
    permission_classes = [IsRWOrGod]
    serializer_class = TestingSerializer
    queryset = Testing.objects.all()
    parser_classes = [MultiPartParser, FormParser]
