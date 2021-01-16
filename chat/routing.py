from django.urls import path

from .consumers import ConversationConsumer

websocket_urlpatterns = [
    path("conversation/<str:username>/", ConversationConsumer.as_asgi()),
]
