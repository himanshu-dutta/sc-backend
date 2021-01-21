import re
from django.contrib.auth.models import User
from main.models import Notification, Post, UserAccount, Connection
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import (
    NotificationSerializer,
    UserAccountSerializer,
    UserSerializer,
    PostSerializer,
    RegisterSerializer,
)

from django.contrib.auth import login
from rest_framework.authtoken.serializers import AuthTokenSerializer
from knox.views import LoginView as KnoxLoginView


from rest_framework.permissions import IsAuthenticatedOrReadOnly
from knox.auth import TokenAuthentication


######################
#   User Account APIs
######################

# Register API
class UserRegistrationAPI(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        print(UserSerializer(user, context=self.get_serializer_context()).data)
        return Response(
            UserSerializer(user, context=self.get_serializer_context()).data
        )


# Login API
class UserLoginAPI(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return super(UserLoginAPI, self).post(request, format=None)


# User Retrievel API
class UserRetrievalAPI(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        user = UserSerializer(request.user)
        user_account = UserAccountSerializer(UserAccount.objects.get(user=request.user))
        user_serialized = dict(user.data)
        user_account_serialized = dict(user_account.data)
        user_serialized.update(user_account_serialized)
        return Response(user_serialized)


##################
#   Content APIs
##################


class PostListAPI(APIView):
    """
    The Enhanced Deepfake Detection Technology will later be integrated in the post method of this API.
    """

    def get(self, request):
        posts = Post.objects.filter(user=request.user.useraccount)
        if not posts.exists():
            return Response({"detail": "No posts exist."}, status.HTTP_404_NOT_FOUND)

        return Response(PostSerializer(posts, many=True).data)

    def post(self, request):
        """
        The API expects the attributes:
            {
                "media" (optional),
                "text" (optional),
            }

        Both can't be null at the same time.
        """
        post_data = request.data
        if "media" not in post_data.keys() and "text" not in post_data.keys():
            return Response({}, status.HTTP_400_BAD_REQUEST)

        post = Post(
            text=post_data["text"] if "text" in post_data.keys() else None,
            media=post_data["media"] if "media" in post_data.keys() else None,
            user=request.user.useraccount,
        )
        post.save()
        return Response(PostSerializer(post).data, status.HTTP_201_CREATED)


class ConnectedUserPostListAPI(APIView):
    def get(self, request, username):
        try:
            useraccount = User.objects.get(username=username).useraccount
            connected_users = Connection.objects.get_connected_users(
                self.user.useraccount
            )

            if useraccount not in connected_users:
                raise Exception

            posts = Post.objects.filter(user=useraccount)

            if not posts.exists():
                return Response(
                    {"detail": "No posts exist."}, status.HTTP_404_NOT_FOUND
                )

            return Response(PostSerializer(posts, many=True).data)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PostAPI(APIView):
    def get(self, request, id):
        try:
            post = Post.objects.get(user=request.user.useraccount, id=id)
            return Response(PostSerializer(post).data)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def put(self, request, id):
        try:
            post = Post.objects.get(user=request.user.useraccount, id=id)
            post_serialized = PostSerializer(post, data=request.data)
            print(post_serialized.initial_data, post_serialized.is_valid())
            post_serialized.is_valid(raise_exception=True)
            post_serialized.save()
            return Response(post_serialized.data)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, id):
        try:
            post = Post.objects.get(user=request.user.useraccount, id=id)
            post.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class FeedAPI(APIView):
    def get(self, request):
        connected_users = Connection.objects.get_connected_users(
            request.user.useraccount
        )
        if not connected_users:
            return Response(status=status.HTTP_204_NO_CONTENT)

        posts = Post.objects.filter(user__in=connected_users)
        print(posts)

        return Response(PostSerializer(posts, many=True), status=status.HTTP_200_OK)


class NotificationListAPI(APIView):
    """
    This API will be used to create a new post, and the allowed types are as follows:
        . like
        . share
        . post
        . report
    """

    def get(self, request):
        user = request.user.useraccount
        notifications = Notification.objects.filter(sent_to__in=[user])
        notifications_serialized = NotificationSerializer(notifications, many=True)
        return Response(notifications_serialized.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        The API expects the attributes:
            {"type", "post_id"}
        """
        try:
            notification_data = request.data
            if (
                not "type" in notification_data.keys()
                or not "post_id" in notification_data.keys()
            ):
                raise Exception("Argument error.")

            notification_type = notification_data["type"]
            post = Post.objects.get(id=notification_data["post_id"])

            connected_users = Connection.objects.get_connected_users(
                request.user.useraccount
            )

            if not connected_users:
                raise Exception("Users not connected.")

            if notification_type == "like":
                if post.user not in connected_users:
                    raise Exception
                notification = Notification.objects.create_like_notification(
                    request.user.useraccount, post
                )

            elif notification_type == "share":
                if post.user not in connected_users:
                    raise Exception

                notification = Notification.objects.create_share_notification(
                    request.user.useraccount, post
                )

            elif notification_type == "report":
                if post.user not in connected_users:
                    raise Exception

                notification = Notification.objects.create_report_notification(
                    request.user.useraccount, post
                )

            elif notification_type == "post":
                if post.user != request.user.useraccount:
                    raise Exception

                notification = Notification.objects.create_post_notification(
                    connected_users, post
                )

            else:
                raise Exception

            notification_serialized = NotificationSerializer(notification)

            return Response(
                notification_serialized.data, status=status.HTTP_201_CREATED
            )

        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)