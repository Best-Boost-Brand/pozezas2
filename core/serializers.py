from rest_framework import serializers
from .models import (
    User, Nomenklatura, Zahon, Chastyna,
    Obladnannya, Vyprobuvannya, Access, Session
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'chastyna']
        read_only_fields = ['id']

class NomenklaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nomenklatura
        fields = ['id', 'name']
        read_only_fields = ['id']

class ZahonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zahon
        fields = ['id', 'name']
        read_only_fields = ['id']

class ChastynaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chastyna
        fields = ['id', 'name', 'description', 'zahon']
        read_only_fields = ['id']

class ObladnannyaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Obladnannya
        fields = ['id', 'nomenklatura', 'inventory_number', 'description', 'chastyna']
        read_only_fields = ['id']

class VyprobuvannyaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vyprobuvannya
        fields = ['id', 'obladnannya', 'test_date', 'result', 'next_test_date', 'act_url']
        read_only_fields = ['id']

class AccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Access
        fields = ['id', 'user', 'zahon', 'chastyna', 'level']
        read_only_fields = ['id']

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'user', 'token', 'ex_time']
        read_only_fields = ['id']

