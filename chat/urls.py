from django.urls import path

from . import views

urlpatterns = [
    path("message/<str:username>/", views.ConversationRetrievalAPI.as_view()),
]
