from rest_framework import serializers

from .models import Message
from main.models import UserAccount


class SenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ("first_name", "last_name")


class ConversationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    first_name = serializers.CharField(max_length=200)
    last_name = serializers.CharField(max_length=200)
    username = serializers.CharField(max_length=200)
    display_picture = serializers.ImageField()
    updated_at = serializers.DateTimeField()


class MessageSerializer(serializers.ModelSerializer):
    sender = SenderSerializer()

    class Meta:
        model = Message
        fields = ("sender", "text", "media", "created_at", "read")
