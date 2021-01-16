from django.urls import path
from knox import views as knox_views

from .views import UserRegistrationAPI, UserLoginAPI

urlpatterns = [
    path("api/register/", UserRegistrationAPI.as_view(), name="user_registration"),
    path("api/login/", UserLoginAPI.as_view(), name="login"),
    path("api/logout/", knox_views.LogoutView.as_view(), name="logout"),
    path("api/logoutall/", knox_views.LogoutAllView.as_view(), name="logoutall"),
]
