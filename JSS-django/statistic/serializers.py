from .models import *
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class TotalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Total
        fields = '__all__'


class D1Serializer(serializers.ModelSerializer):
    class Meta:
        model = D1
        fields = '__all__'


class D2Serializer(serializers.ModelSerializer):
    class Meta:
        model = D2
        fields = '__all__'


class D3Serializer(serializers.ModelSerializer):
    class Meta:
        model = D3
        fields = '__all__'


class D4Serializer(serializers.ModelSerializer):
    class Meta:
        model = D4
        fields = '__all__'


class CustomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Custom
        fields = '__all__'


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'


class ResSerializer(serializers.ModelSerializer):
    class Meta:
        model = Res
        fields = '__all__'


class OrganSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organ
        fields = '__all__'


class DeptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dept
        fields = '__all__'


class SuccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Success
        fields = '__all__'


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = '__all__'


class ReportCustomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCustom
        fields = '__all__'
