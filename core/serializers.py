from rest_framework import serializers
from django.utils import timezone
from django.utils.text import slugify

from .models import (
    Brigade, Detachment, User, UserSession, Nomenclature, Equipment, Testing
)

# ===================== helpers =====================

def _guess_category(name: str) -> str:
    n = (name or "").lower()
    if "драб" in n:
        return "драбини"
    if "мотуз" in n:
        return "мотузки"
    if "рукав" in n:
        return "рукавиці"
    if "ремен" in n:
        return "ремені"
    return "інше"


def _unique_slug(base: str) -> str:
    base = slugify(base or "item", allow_unicode=True) or "item"
    slug = base
    i = 2
    while Nomenclature.objects.filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug


# ===================== Auth =====================

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class SessionOutSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    brigadeId = serializers.IntegerField(allow_null=True, required=False)
    detachments = serializers.ListField(child=serializers.IntegerField(), required=False)


# ===================== Admin =====================

class BrigadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brigade
        fields = ("id", "name")


class DetachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Detachment
        fields = ("id", "name")


class UserRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    confirmPassword = serializers.CharField()
    mode = serializers.ChoiceField(choices=[("RO","RO"),("RW","RW"),("GOD","GOD")])
    brigade = serializers.IntegerField(required=False, allow_null=True)
    detachments = serializers.ListField(child=serializers.IntegerField(), required=False)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirmPassword"]:
            raise serializers.ValidationError({"confirmPassword":"Passwords do not match"})
        return attrs


# ===================== Nomenclature =====================

class NomenclatureOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenclature
        fields = ("id","name","category","slug","unit","active")


class NomenclatureCreateSerializer(serializers.ModelSerializer):
    """
    Створення номенклатури одним полем `name`.
    Інші поля заповнюються автоматично.
    """
    name = serializers.CharField()
    category = serializers.CharField(required=False, allow_blank=True)
    slug = serializers.CharField(required=False, allow_blank=True)
    unit = serializers.CharField(required=False, default="шт")
    active = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = Nomenclature
        fields = ("id","name","category","slug","unit","active")

    def create(self, validated_data):
        name = validated_data["name"]
        if not validated_data.get("category"):
            validated_data["category"] = _guess_category(name)
        if not validated_data.get("slug"):
            validated_data["slug"] = _unique_slug(name)
        if not validated_data.get("unit"):
            validated_data["unit"] = "шт"
        if "active" not in validated_data:
            validated_data["active"] = True
        return super().create(validated_data)


class NomenclatureCategoryOutSerializer(serializers.Serializer):
    code = serializers.CharField()
    slug = serializers.CharField()
    name = serializers.CharField()


# ===================== Equipment =====================

class EquipmentSerializer(serializers.ModelSerializer):
    brigade = serializers.PrimaryKeyRelatedField(queryset=Brigade.objects.all())
    nomenclatureId = serializers.IntegerField(source="nomenclature_id", required=False, allow_null=True)
    detachment = serializers.PrimaryKeyRelatedField(queryset=Detachment.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Equipment
        fields = ("id","inventory_number","name","type","brigade","nomenclatureId","description","detachment")


class BrigadeEquipmentCreateSerializer(serializers.Serializer):
    """
    Приймає або `nomenclatureId`, або `nomenclatureName`.
    Якщо передано name — знайдемо/створимо номенклатуру і підкладемо її в _nomenclature.
    """
    nomenclatureId = serializers.IntegerField(required=False)
    nomenclatureName = serializers.CharField(required=False)
    inventory_number = serializers.CharField(max_length=50)
    description = serializers.CharField(allow_blank=True, required=False, default="")
    detachment = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        nom_id = attrs.get("nomenclatureId")
        nom_name = attrs.get("nomenclatureName")

        if not nom_id and not nom_name:
            raise serializers.ValidationError({"nomenclatureId": "Передайте або nomenclatureId, або nomenclatureName"})

        # знайти/створити номенклатуру
        if nom_id:
            try:
                n = Nomenclature.objects.get(id=nom_id, active=True)
            except Nomenclature.DoesNotExist:
                raise serializers.ValidationError({"nomenclatureId":"Not found"})
        else:
            n, _ = Nomenclature.objects.get_or_create(
                name=nom_name,
                defaults={
                    "category": _guess_category(nom_name),
                    "slug": _unique_slug(nom_name),
                    "unit": "шт",
                    "active": True,
                }
            )
        attrs["_nomenclature"] = n
        return attrs


# ===================== Testing =====================

class TestingSerializer(serializers.ModelSerializer):
    equipment = serializers.PrimaryKeyRelatedField(queryset=Equipment.objects.all())

    class Meta:
        model = Testing
        fields = ("id","equipment","date","result","next_date","external_url","file")


# Java style payload
class JavaTestingInSerializer(serializers.Serializer):
    deviceInventoryNumber = serializers.CharField()
    testingDate = serializers.IntegerField()      # epoch ms
    testingResult = serializers.CharField()
    nextTestingDate = serializers.IntegerField(required=False, allow_null=True)
    url = serializers.URLField(required=False, allow_blank=True)

    def to_internal_value(self, data):
        obj = super().to_internal_value(data)
        # convert ms to date
        from datetime import datetime
        obj["date"] = datetime.utcfromtimestamp(obj.pop("testingDate")/1000.0).date()
        nd = obj.pop("nextTestingDate", None)
        if nd:
            obj["next_date"] = datetime.utcfromtimestamp(nd/1000.0).date()
        else:
            obj["next_date"] = None
        obj["result"] = obj.pop("testingResult")
        obj["external_url"] = obj.pop("url", None)
        return obj


class JavaTestingOutSerializer(serializers.Serializer):
    testingId = serializers.IntegerField()
    deviceInventoryNumber = serializers.CharField()
    testingDate = serializers.IntegerField()
    testingResult = serializers.CharField()
    nextTestingDate = serializers.IntegerField(allow_null=True)
    url = serializers.CharField(allow_blank=True, allow_null=True)


class JavaTestingListOutSerializer(serializers.Serializer):
    testingItems = JavaTestingOutSerializer(many=True)


class JavaEquipmentTypeOutSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField(allow_blank=True)
