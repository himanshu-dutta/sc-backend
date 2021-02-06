from os import stat
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.db.transaction import atomic
from rest_framework import response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import generics, status
from main.models import Notification, Post, PostInteraction, UserAccount, Connection
from .serializers import (
    ConnectedUserSerializer,
    ConnectionSerializer,
    NotificationSerializer,
    UserAccountSerializer,
    UserProfileSerializer,
    UserSerializer,
    PostSerializer,
    RegisterSerializer,
)

from django.contrib.auth import login
from rest_framework.authtoken.serializers import AuthTokenSerializer
from knox.views import LoginView as KnoxLoginView


from rest_framework.permissions import IsAuthenticated, AllowAny
from knox.auth import TokenAuthentication


######################
#   User Account APIs
######################

# Register API
class UserRegistrationAPI(generics.GenericAPIView):
    """
    For users to create a new account on the service.
    Allowed Methods: POST
    """

    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user, context=self.get_serializer_context()).data
        )


# Login API
class UserLoginAPI(KnoxLoginView):
    """
    For users to log into their account.
    Allowed Methods: POST
    """

    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return super(UserLoginAPI, self).post(request, format=None)


# User Retrievel API
class UserRetrievalAPI(APIView):
    """
    To retrieve details of own account for the logged in user.
    Allowed Methods: GET
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = UserSerializer(request.user)
        user_account = UserAccountSerializer(UserAccount.objects.get(user=request.user))
        user_serialized = dict(user.data)
        user_account_serialized = dict(user_account.data)
        user_serialized.update(user_account_serialized)
        return Response(user_serialized)


class UserProfileViewAPI(APIView):
    """
    For users to retrieve details of another account, other than themselves,
    Allowed Methods: GET
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
            user_account = UserProfileSerializer(user.useraccount)
            user = UserSerializer(user)
            user_serialized = dict(user.data)
            user_account_serialized = dict(user_account.data)
            user_serialized.update(user_account_serialized)
            return Response(user_serialized)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


##################
#   Content APIs
##################


class PostListAPI(APIView):
    """
    Lists all the post created by the logged in user.
    Allowed Methods: GET, POST.
    TODO: The Enhanced Deepfake Detection Technology will later be integrated in the POST method of this API.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

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
            return Response(
                {
                    "detail": "both the text and media for the post can't be empty at the same time."
                },
                status.HTTP_400_BAD_REQUEST,
            )

        post = Post(
            text=post_data["text"] if "text" in post_data.keys() else None,
            media=post_data["media"] if "media" in post_data.keys() else None,
            user=request.user.useraccount,
        )
        post.save()
        return Response(PostSerializer(post).data, status.HTTP_201_CREATED)


class ConnectedUserPostListAPI(APIView):
    """
    Lists all the posts by a connected user, given the username.
    Allowed Methods: GET
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        try:
            useraccount = User.objects.get(username=username).useraccount
            connected_users = Connection.objects.get_connected_users(
                request.user.useraccount
            )

            if useraccount not in connected_users:
                raise Exception

            posts = Post.objects.filter(user=useraccount)

            if not posts.exists():
                return Response(
                    {"detail": "No posts exist."}, status.HTTP_404_NOT_FOUND
                )

            return Response(PostSerializer(posts, many=True).data)
        except KeyboardInterrupt:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PostInteractionAPI(APIView):
    """
    Allows the logged in user to interact with a post created by a connected user.
    Allowed Methods: PUT
    Posible interactions: LIKE, REPORT
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @atomic
    def put(self, request, id, type):
        try:
            post = Post.objects.get(id=id)
            useraccount = post.user

            connected_users = Connection.objects.get_connected_users(
                request.user.useraccount
            )
            if useraccount not in connected_users:
                return Response(
                    {"detail": "Can't interact with posts of unconnected users."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            post_interaction = PostInteraction.objects.filter(
                post=post, user=request.user.useraccount
            )

            if not post_interaction.exists():
                post_interaction = PostInteraction(
                    post=post, user=request.user.useraccount
                )
            else:
                post_interaction = post_interaction.first()

            if type == "like":
                if post_interaction.like:
                    post.likes -= 1
                    post_interaction.like = False
                    Notification.objects.delete_notification(
                        "like", request.user.useraccount, post
                    )
                else:
                    post.likes += 1
                    post_interaction.like = True
                    Notification.objects.create_like_notification(
                        request.user.useraccount, post
                    )

            if type == "report":
                if post_interaction.report:
                    post.reports -= 1
                    post_interaction.report = False
                    Notification.objects.delete_notification(
                        "report", request.user.useraccount, post
                    )
                else:
                    post.reports += 1
                    post_interaction.report = True
                    Notification.objects.create_report_notification(
                        request.user.useraccount, post
                    )

            post.save()
            post_interaction.save()

            post_serialized = PostSerializer(post)
            return Response(post_serialized.data)

        except Post.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PostAPI(APIView):
    """
    Allows the logged in user to create, edit or delete a post, as per their choice.
    Allowed Methods: GET, PUT, DELETE
    TODO: The Enhanced Deepfake Detection Technology will later be integrated in the PUT method of this API.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

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
    """
    API to retrieve all the recent posts by connected users.
    Allowed Methods: GET
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        connected_users = Connection.objects.get_connected_users(
            request.user.useraccount
        )
        if not connected_users:
            return Response(status=status.HTTP_204_NO_CONTENT)

        posts = Post.objects.filter(user__in=connected_users)

        return Response(
            PostSerializer(posts, many=True).data, status=status.HTTP_200_OK
        )


class NotificationListAPI(APIView):
    """
    This API will be used to create a new notification, and retrieve all the recent notifications for the logged in user.
    Allowed Methods: GET, POST
    Possible Notification Types: LIKE, SHARE, POST, REPORT
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

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
                raise Exception("Attribute error.")

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
            return Response(
                {
                    "detail": "Either the attributes are wrong, or the user is not in connection, or the type of notification attempted to create has errors."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


####################
#   Connection APIs
####################


class ConnectionsListAPI(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        connected_useraccounts = Connection.objects.get_connected_users(
            request.user.useraccount
        )

        if not len(connected_useraccounts):
            return Response(status=status.HTTP_204_NO_CONTENT)

        connected_useraccounts_serialized = ConnectedUserSerializer(
            connected_useraccounts, many=True
        ).data

        return Response(connected_useraccounts_serialized, status=status.HTTP_200_OK)


class ConnectionsAPI(APIView):
    def delete(self, request, username):
        try:
            user = User.objects.get(username=username)

            Connection.objects.delete_connection(
                request.user.useraccount, user.useraccount
            )

            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(
                {"details": "Invalid username."}, status=status.HTTP_400_BAD_REQUEST
            )


class ConnectionRequestListAPI(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        connection_requests = Connection.objects.filter(
            users__in=[request.user.useraccount], accepted=False
        )

        if not connection_requests.exists():
            return Response(status=status.HTTP_204_NO_CONTENT)

        connection_requests_serialized = ConnectionSerializer(
            connection_requests, many=True
        ).data

        return Response(connection_requests_serialized, status=status.HTTP_200_OK)


class ConnectionRequestAPI(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        """
        For sending connection request to other user.
        """
        try:
            user = User.objects.get(username=username)

            Connection.objects.create_connection_request(
                request.user.useraccount, user.useraccount
            )

            return Response(status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {"details": "Invalid username."}, status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, username):
        """
        For deleting sent connection request to other user.
        """
        try:
            user = User.objects.get(username=username)

            Connection.objects.delete_connection(
                request.user.useraccount, user.useraccount, False
            )

            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(
                {"details": "Invalid username."}, status=status.HTTP_400_BAD_REQUEST
            )


class ConnectionRequestResponseAPI(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, username, accept):
        """
        For accepting/declining a connection request.
        Only valid keywords for accept parameter:
        {
            "accept",
            "decline"
        }
        """
        try:
            if accept != "accept" and accept != "decline":
                raise Exception("Invalid Argument")

            if accept == "accept":
                accept = True
            else:
                accept = False

            user = User.objects.get(username=username)

            Connection.objects.accept_decline(
                user.useraccount, request.user.useraccount, accept
            )

            return Response(status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {"details": "Invalid username."}, status=status.HTTP_400_BAD_REQUEST
            )
        except ObjectDoesNotExist:
            return Response(
                {"details": "No such connection request exists."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception:
            return Response(
                {"details": "Invalid argument."}, status=status.HTTP_400_BAD_REQUEST
            )


class SuggestedUserAPI(APIView):
    """
    TODO: Implementation pending until a further research over implementation.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pass
