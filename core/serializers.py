from rest_framework import serializers
from .models import User, Brigade, Detachment, Equipment, Testing

# -------- AUTH --------
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    brigade = serializers.IntegerField(required=False, write_only=True)
    detachments = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )

class LoginResponseSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    mode = serializers.CharField()
    brigade = serializers.CharField(allow_null=True)
    detachments = serializers.ListField(child=serializers.CharField())

# -------- CORE --------
class BrigadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brigade
        fields = ['id', 'name']

class DetachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Detachment
        fields = ['id', 'name']

class EquipmentSerializer(serializers.ModelSerializer):
    brigade_name = serializers.CharField(source='brigade.name', read_only=True)

    class Meta:
        model = Equipment
        fields = ['id', 'inventory_number', 'name', 'type', 'brigade', 'brigade_name']

class TestingSerializer(serializers.ModelSerializer):
    brigade = serializers.SerializerMethodField()
    equipment_type = serializers.CharField(source='equipment.type', read_only=True)

    class Meta:
        model = Testing
        fields = ['id', 'equipment', 'brigade', 'tested_by', 'date', 'result', 'next_date', 'file', 'equipment_type']

    def get_brigade(self, obj):
        return obj.equipment.brigade.name if obj.equipment and obj.equipment.brigade else None

    def validate(self, data):
        user = self.context['request'].user
        equipment = data.get('equipment')

        if user.mode != 'GOD':
            if not equipment or equipment.brigade != user.brigade:
                raise serializers.ValidationError("Ви не маєте доступу до цього обладнання.")
        return data
