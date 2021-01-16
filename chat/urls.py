from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<str:username>/", views.conversation, name="conversation"),
    path("message/<str:username>/", views.ConversationRetrievalAPI.as_view()),
]
