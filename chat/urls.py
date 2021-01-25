from django.urls import path

from .views import ConversationAPI, MessagesAPI, ConversationListAPI

urlpatterns = [
    path("api/conversations", ConversationListAPI.as_view()),
    path("api/conversation/<str:username>", ConversationAPI.as_view()),
    path("api/message/<str:sent_to>/", MessagesAPI.as_view()),
]
