from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


from main.models import UserAccount
from django.db.transaction import atomic
from .models import Conversation, Message
from django.contrib.auth.models import User
from .serializers import ConversationSerializer, MessageSerializer


class ConversationListAPI(APIView):
    """
    Lists all the previously initiated conversations with connected users of the logged in user.
    Allowed Methods: GET
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations, conversations_with = Conversation.objects.by_user(
            request.user.useraccount
        )

        if not conversations_with or not conversations.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        open_conversations_with = []
        for conversation, useraccount in zip(conversations, conversations_with):
            open_conversations_with.append(
                {
                    "name": conversation.name,
                    "first_name": useraccount.first_name,
                    "last_name": useraccount.last_name,
                    "display_picture": useraccount.display_picture,
                    "username": useraccount.user.username,
                    "updated_at": conversation.updated_at,
                }
            )

        conversations_serialized = ConversationSerializer(
            data=open_conversations_with, many=True
        )
        conversations_serialized.is_valid(raise_exception=True)

        return Response(conversations_serialized.data)


class ConversationAPI(APIView):
    """
    API to initiate a new conversation or delete any conversation previously initiated.
    Allowed Methods: POST, DELETE
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, username):

        sender = request.user.useraccount
        receiver = UserAccount.objects.get(user=User.objects.get(username=username))
        conversation = Conversation.objects.get_or_create_conversation(sender, receiver)

        conversation_serialized = ConversationSerializer(
            data={
                "name": conversation.name,
                "first_name": receiver.first_name,
                "last_name": receiver.last_name,
                "display_picture": receiver.display_picture,
                "username": receiver.user.username,
                "updated_at": conversation.updated_at,
            }
        )
        conversation_serialized.is_valid(raise_exception=True)

        return Response(conversation_serialized.data)

    def delete(self, request, username):

        sender = request.user.useraccount
        receiver = UserAccount.objects.get(user=User.objects.get(username=username))
        conversation = Conversation.objects.get_or_create_conversation(sender, receiver)
        conversation.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class MessagesAPI(APIView):
    """
    API to retrieve all the messages belonging to a particular conversation.
    Allowed Methods: GET
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @atomic
    def get(self, request, sent_to):
        sender = request.user.useraccount
        receiver = UserAccount.objects.get(user=User.objects.get(username=sent_to))
        conversation = Conversation.objects.get_or_create_conversation(sender, receiver)
        messages = Message.objects.filter(conversation=conversation)
        for message in messages:
            if message.sender != sender:
                message.read = True
                message.save()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
