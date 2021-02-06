from django.db import transaction
from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Connection, Notification, Post, UserAccount

from datetime import date


###################
# Custom mixins
###################


class FlattenMixin(object):
    """
    Flatens the specified related objects in this representation
    src: https://stackoverflow.com/questions/21381700/django-rest-framework-how-do-you-flatten-nested-data
    """

    def to_representation(self, obj):
        assert hasattr(
            self.Meta, "flatten"
        ), 'Class {serializer_class} missing "Meta.flatten" attribute'.format(
            serializer_class=self.__class__.__name__
        )
        # Get the current object representation
        rep = super(FlattenMixin, self).to_representation(obj)
        # Iterate the specified related objects with their serializer
        for field, serializer_class in self.Meta.flatten:
            serializer = serializer_class(context=self.context)
            objrep = serializer.to_representation(getattr(obj, field))
            # Include their fields, prefixed, in the current   representation
            for key in objrep:
                rep[key] = objrep[key]
        return rep


# UserAccount Serializer
class UserAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = (
            "first_name",
            "last_name",
            "display_picture",
            "phone",
            "date_of_birth",
            "profile_summary",
        )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ("first_name", "last_name", "display_picture", "profile_summary")


# User Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email")


# Register Serializer
class RegisterSerializer(serializers.ModelSerializer):
    user_account = UserAccountSerializer(required=True)

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


# Post Serializer
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "text", "media", "likes", "created_at")


# Notification Serializer
class NotificationSerializer(serializers.ModelSerializer):
    post = PostSerializer()

    class Meta:
        model = Notification
        fields = ("id", "post", "notification_type", "url", "text", "created_at")


# Connection Serializer
class ConnectedUserSerializer(FlattenMixin, serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = (
            "first_name",
            "last_name",
            "display_picture",
        )

        flatten = [("user", UserSerializer)]


class ConnectionSerializer(FlattenMixin, serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = ("created_at",)
        flatten = [("sent_by", ConnectedUserSerializer)]
