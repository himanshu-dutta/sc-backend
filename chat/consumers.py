from main.models import UserAccount
from asgiref.sync import sync_to_async
from .models import Conversation, Message
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser

import json


class ConversationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if isinstance(self.scope["user"], AnonymousUser):
            raise ValidationError("Anonymous User not allowed.")

        connecting_user = await sync_to_async(UserAccount.objects.get)(
            user=self.scope["user"]
        )

        other_username = self.scope["url_route"]["kwargs"]["username"]

        other_user = None
        try:
            other_user = await sync_to_async(User.objects.get)(username=other_username)
            other_user = await sync_to_async(UserAccount.objects.get)(user=other_user)

        except User.DoesNotExist:
            raise ObjectDoesNotExist("The user doesn't exist.")

        self.conversation = await sync_to_async(
            Conversation.objects.get_or_create_conversation
        )(connecting_user, other_user)

        self.conversation_name = self.conversation.name

        await self.accept()

        await self.channel_layer.group_add(self.conversation_name, self.channel_name)

        await self.channel_layer.group_send(
            self.conversation_name,
            {
                "type": "confirm_connection",
                "message": "connection established",
            },
        )

    async def confirm_connection(self, event):
        message = event["message"]

        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                }
            )
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.conversation_name, self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        text = text_data_json["text"]
        media = text_data_json["media"]
        sendername = text_data_json["sender"]

        sender = await sync_to_async(UserAccount.objects.get)(user=self.scope["user"])

        await self.save_message(sender, text, media)

        await self.channel_layer.group_send(
            self.conversation_name,
            {
                "type": "send_message",
                "text": text,
                "media": media,
                "sender": sender.first_name,
            },
        )

    async def send_message(self, event):
        text = event["text"]
        media = event["media"]
        sender = event["sender"]

        await self.send(
            text_data=json.dumps(
                {
                    "text": text,
                    "media": media,
                    "sender": sender,
                }
            )
        )

    @database_sync_to_async
    def save_message(self, sender, text, media):
        message = Message.objects.save_message(self.conversation, sender, text, media)
        self.conversation.updated_at = message.updated_at
        self.conversation.save()
