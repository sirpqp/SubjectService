from .models import *
from rest_framework import serializers


class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = '__all__'


class BuddySerializer(serializers.ModelSerializer):
    class Meta:
        model = Buddy
        fields = '__all__'


class DialogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dialog
        fields = '__all__'