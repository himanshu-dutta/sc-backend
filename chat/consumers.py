from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Conversation, Message
from main.models import UserAccount
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
import json
from django.contrib.auth.models import AnonymousUser


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
                "type": "tester_message",
                "tester": "hello world",
            },
        )

    async def tester_message(self, event):
        tester = event["tester"]

        await self.send(
            text_data=json.dumps(
                {
                    "tester": tester,
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

        previous_messages = await self.get_messages()

        await self.save_message(sender, text, media)

        await self.channel_layer.group_send(
            self.conversation_name,
            {
                "type": "send_message",
                "text": text,
                "media": media,
                "sender": sendername,
                "previous_messages": previous_messages,
            },
        )

    async def send_message(self, event):
        text = event["text"]
        media = event["media"]
        sender = event["sender"]
        previous_messages = event["previous_messages"]

        # print(previous_messages)

        await self.send(
            text_data=json.dumps(
                {
                    "text": text,
                    "media": media,
                    "sender": sender,
                    "previous_messages": previous_messages,
                }
            )
        )

    @database_sync_to_async
    def get_messages(self):
        return Message.objects.get_messages(self.conversation)

    @database_sync_to_async
    def save_message(self, sender, text, media):
        Message.objects.save_message(self.conversation, sender, text, media)
