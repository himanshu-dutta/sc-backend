from django.db import models
from django.template.defaultfilters import slugify

from main.models import TrackingModel, UserAccount
from .managers import ConversationManager, MessageManager


def get_media_path(instance, filename):
    return f"media/user/{slugify(instance.sender.username)}/conversation/{filename}"


class Conversation(TrackingModel):

    name = models.CharField(max_length=50, primary_key=True)
    users = models.ManyToManyField(UserAccount, related_name="conversation_between")

    objects = ConversationManager()

    def __str__(self):
        return f"{self.users.first()} and {self.users.last()}"


class Message(TrackingModel):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )

    sender = models.ForeignKey(UserAccount, on_delete=models.CASCADE)

    text = models.TextField(blank=False, null=False)

    media = models.FileField(upload_to=get_media_path, blank=True, null=True)

    read = models.BooleanField(default=False)

    objects = MessageManager()

    def __str__(self):
        return f"From <Thread - {self.conversation}>"
