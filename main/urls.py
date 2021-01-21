from django.urls import path
from knox import views as knox_views

from .views import (
    ConnectedUserPostListAPI,
    FeedAPI,
    NotificationListAPI,
    PostListAPI,
    PostAPI,
    UserRegistrationAPI,
    UserLoginAPI,
    UserRetrievalAPI,
)

urlpatterns = [
    # user account
    path("api/register/", UserRegistrationAPI.as_view(), name="user_registration"),
    path("api/login/", UserLoginAPI.as_view(), name="login"),
    path("api/logout/", knox_views.LogoutView.as_view(), name="logout"),
    path("api/logoutall/", knox_views.LogoutAllView.as_view(), name="logoutall"),
    path("api/userdetail/", UserRetrievalAPI.as_view(), name="userdetail"),

    # posts
    path("api/content/post/", PostListAPI.as_view(), name="postlist"),
    path("api/content/post/<int:id>/", PostAPI.as_view(), name="post"),
    path(
        "api/content/post/<int:username>/",
        ConnectedUserPostListAPI.as_view(),
        name="connected_user_post",
    ),
    path("api/content/feed/", FeedAPI.as_view(), name="feed"),
    
    # notifications
    path(
        "api/content/notifications/",
        NotificationListAPI.as_view(),
        name="notifications",
    ),
]
