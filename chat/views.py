from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response

from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from main.models import UserAccount
from .models import Conversation, Message
from .serializers import MessageSerializer


class ConversationRetrievalAPI(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, sent_to):
        sender = UserAccount.objects.get(user=request.user)
        receiver = UserAccount.objects.get(user=User.objects.get(username=sent_to))
        conversation = Conversation.objects.get_or_create_conversation(sender, receiver)
        messages = Message.objects.filter(conversation=conversation)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
