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
        fields = ['id', 'code', 'name']

class TestingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testing
        fields = ['id', 'brigade', 'equipment', 'tested_by', 'tested_at', 'result', 'notes']

    def validate(self, data):
        user = self.context['request'].user
        if user.mode != 'GOD' and user.brigade != data['brigade']:
            raise serializers.ValidationError("Ви не маєте доступу до цієї бригади.")
        return data