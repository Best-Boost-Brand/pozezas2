from rest_framework import serializers
from .models import User, Brigade, Detachment, Equipment, Testing

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
    brigade = serializers.CharField()
    detachments = serializers.ListField(child=serializers.CharField())

class BrigadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brigade
        fields = ['id', 'name']

class DetachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Detachment
        fields = ['id', 'name', 'brigade', 'users']

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['id', 'inventory_number', 'name', 'type', 'brigade']


class TestingSerializer(serializers.ModelSerializer):
    tested_by = serializers.StringRelatedField(read_only=True)
    brigade = serializers.SerializerMethodField()

    class Meta:
        model = Testing
        fields = ['id', 'equipment', 'brigade', 'tested_by', 'date', 'result', 'next_date', 'file']

    def get_brigade(self, obj):
        return obj.equipment.brigade.name if obj.equipment and obj.equipment.brigade else None

    def validate(self, data):
        user = self.context['request'].user
        equipment = data.get('equipment')

        if user.mode != 'GOD':
            if not equipment or equipment.brigade != user.brigade:
                raise serializers.ValidationError("Ви не маєте доступу до цього обладнання.")
        return data
