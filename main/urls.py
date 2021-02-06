from django.urls import path
from knox import views as knox_views

from .views import (
    ConnectedUserPostListAPI,
    ConnectionRequestAPI,
    ConnectionRequestListAPI,
    ConnectionRequestResponseAPI,
    ConnectionsAPI,
    ConnectionsListAPI,
    FeedAPI,
    NotificationListAPI,
    PostInteractionAPI,
    PostListAPI,
    PostAPI,
    UserProfileViewAPI,
    UserRegistrationAPI,
    UserLoginAPI,
    UserRetrievalAPI,
)

urlpatterns = [
    # user account
    path("api/user/register/", UserRegistrationAPI.as_view(), name="user_registration"),
    path("api/user/login/", UserLoginAPI.as_view(), name="login"),
    path("api/user/logout/", knox_views.LogoutView.as_view(), name="logout"),
    path("api/user/logoutall/", knox_views.LogoutAllView.as_view(), name="logoutall"),
    path("api/user/userdetail/", UserRetrievalAPI.as_view(), name="user_detail"),
    path(
        "api/user/userprofile/<str:username>/",
        UserProfileViewAPI.as_view(),
        name="user_profle",
    ),
    # posts
    path("api/content/post/", PostListAPI.as_view(), name="post_list"),
    path("api/content/post/<int:id>/", PostAPI.as_view(), name="post"),
    path(
        "api/content/post/interact/<int:id>/<str:type>",
        PostInteractionAPI.as_view(),
        name="post_interaction",
    ),
    path(
        "api/content/post/<str:username>",
        ConnectedUserPostListAPI.as_view(),
        name="connected_user_post",
    ),
    path("api/content/feed/", FeedAPI.as_view(), name="feed"),
    # notifications
    path(
        "api/content/notification/",
        NotificationListAPI.as_view(),
        name="notification_list",
    ),
    # connections
    path(
        "api/connections/connections/",
        ConnectionsListAPI.as_view(),
        name="connection_list",
    ),
    path(
        "api/connections/delete/<str:username>/",
        ConnectionsAPI.as_view(),
        name="connection_delete",
    ),
    path(
        "api/connections/connectionrequest/",
        ConnectionRequestListAPI.as_view(),
        name="connection_request_list",
    ),
    path(
        "api/connections/connectionrequest/<str:username>",
        ConnectionRequestAPI.as_view(),
        name="connection_request",
    ),
    path(
        "api/connections/connectionrequestresponse/<str:username>/<str:accept>/",
        ConnectionRequestResponseAPI.as_view(),
        name="connection_request_response",
    ),
]
