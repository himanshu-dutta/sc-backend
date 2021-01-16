from django.contrib.auth.models import User
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from knox.auth import TokenAuthentication

from .models import Conversation, Message
from main.models import UserAccount
from .serializers import MessageSerializer

# Create your views here.


def index(request):
    return render(request, "index.html", {})


def conversation(request, username):
    return render(
        request,
        "conversation.html",
        {
            "username": username,
        },
    )


class ConversationRetrievalAPI(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, username):
        sender = UserAccount.objects.get(user=request.user)
        receiver = UserAccount.objects.get(user=User.objects.get(username=username))
        conversation = Conversation.objects.get_or_create_conversation(sender, receiver)
        messages = Message.objects.filter(conversation=conversation)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
