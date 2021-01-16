import json
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import connection, models

from django.core import serializers
from main.models import Connection


class ConversationManager(models.Manager):
    def get_or_create_conversation(self, user1, user2):
        connection = (
            Connection.objects.filter(users=user1)
            .filter(users=user2)
            .filter(accepted=True)
            .distinct()
        )

        if not connection.exists():
            raise ObjectDoesNotExist("No connection exists between the users.")

        conversations = (
            self.get_queryset().filter(users=user1).filter(users=user2).distinct()
        )

        if not conversations.exists():
            conversation = self.create(name=f"{user1.first_name}-{user2.first_name}")
            conversation.users.add(user1)
            conversation.users.add(user2)
            return conversation

        return conversations.first()

    def by_user(self, user):
        return self.get_queryset().filter(users__in=[user])


class MessageManager(models.Manager):
    def save_message(self, conversation, sender, text=None, media=None):
        if not text and not media:
            raise ValidationError("Can't send message without tet and media.")
        if sender not in conversation.users.all():
            raise ValidationError(
                "Can't send message to a conversation if the sender is not part of it."
            )

        self.create(conversation=conversation, sender=sender, text=text, media=media)

    def get_messages(self, conversation):
        messages = serializers.serialize(
            "json",
            self.get_queryset().filter(conversation=conversation),
            fields=[
                "sender__first_name",
                "sender__last_name",
                "text",
                "created_at",
                "read",
                "media",
            ],
        )
        messages = json.loads(messages)
        messages_json = json.dumps([message["fields"] for message in messages])

        return messages_json
