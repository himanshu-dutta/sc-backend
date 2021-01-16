from knox.auth import User
from rest_framework import serializers

from .models import Message
from main.models import UserAccount


class SenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ("first_name", "last_name")


class MessageSerializer(serializers.ModelSerializer):
    sender = SenderSerializer()

    class Meta:
        model = Message
        fields = (
            "sender",
            "text",
            "created_at",
            "read",
            "media",
        )
