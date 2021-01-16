from enum import unique
from rest_framework import serializers
from django.db import transaction
from django.contrib.auth.models import User

from .models import UserAccount

from datetime import date

# UserAccount Serializer
class UserAccountSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField()

    class Meta:
        model = UserAccount
        fields = ("first_name", "last_name", "phone", "date_of_birth")


# User Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


# Register Serializer
class RegisterSerializer(serializers.ModelSerializer):
    user_account = UserAccountSerializer(required=True)
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "user_account")
        extra_kwargs = {"password": {"write_only": True}}

    @transaction.atomic
    def create(self, validated_data):
        user_account_details = validated_data.pop("user_account")
        self.vaidate_email(validated_data["email"])
        self.validate_dob(user_account_details["date_of_birth"])

        user = User.objects.create_user(
            validated_data["username"],
            validated_data["email"],
            validated_data["password"],
        )

        user_account = UserAccount.objects.create(user=user, **user_account_details)

        return user

    def vaidate_email(self, email):
        if User.objects.filter(email__iexact=email.lower()).exists():
            raise serializers.ValidationError(
                "User with this email is already registered."
            )

    def validate_dob(self, dob):
        today = date.today()

        if (today - dob).days // 365 < 18:
            raise serializers.ValidationError("User can't be below 18 years of age.")
