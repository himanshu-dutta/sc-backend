import random

from django.db import models
from django.db.transaction import atomic
from django.core.exceptions import ObjectDoesNotExist, ValidationError


class ConnectionManager(models.Manager):
    """
    Only these methods are supposed to be used for
    any interaction with the Connection models, no other interaction is allowed.
    """

    @atomic
    def create_connection_request(self, sender, receiver):
        if sender == receiver:
            raise ValidationError("Both users can't be same.")

        connections = self.get_queryset().filter(users__in=[sender, receiver])

        if not connections.exists():
            connection_request = self.create(sent_by=sender)
            connection_request.users.add(sender)
            connection_request.users.add(receiver)
            return connection_request

        return connections.first()

    @atomic
    def accept_decline(self, sender, receiver, accept=False):
        connections = self.get_queryset().filter(users__in=[sender, receiver])

        if connections.exists():
            selected_connection = connections.first()
            if accept:
                selected_connection.accepted = True
                selected_connection.save()

            elif not selected_connection.accepted:
                selected_connection.delete()

        else:
            raise ObjectDoesNotExist("No such connection request exists")

    def delete_connection(self, sender, receiver):
        # in case a user changes their mind to send the request through
        connections = self.get_queryset().filter(users__in=[sender, receiver])

        if connections.exists():
            connections.first().delete()

    def get_connected_users(self, user):
        connections = self.get_queryset().filter(users__in=[user], accepted=True)
        if not connections.exists():
            return None

        connected_users = []

        for connection in connections:
            users = connection.users.all()
            connected_user = ((users.first() != user) and users.first()) or (
                (users.last() != user) and users.last()
            )
            connected_users.append(connected_user)

        return connected_users


class NotificationManager(models.Manager):
    """
    select one of the listed notification choices to keep the notification less mundane
    mapping for formatting:
    sender: s
    receiver: r
    post: p
    """

    LIKE_TEXT_CHOICES = [
        "Hey there, your recent post got liked by {s}",  # example
    ]
    SHARE_TEXT_CHOICES = [
        "Hey {r}, {s} just shared your post.",  # example
    ]
    REPORT_TEXT_CHOICES = [
        "Unfortunately, your post has been reported for violation.",  # example
    ]
    POST_TEXT_CHOICES = [
        "{s} recently shared a post, check it out.",  # example
    ]

    """
        Only these methods are supposed to be used to create different notifications.
        For like, share and report, the post must belong to the receiver, whereas for the post notification, the post should belong to the sender.

    """

    @atomic
    def create_like_notification(self, sender, post):
        receiver = post.user
        notifications = self.get_queryset().filter(
            notification_type="like", sent_by=sender, sent_to__in=[receiver], post=post
        )

        if not notifications.exists():
            text = random.choice(self.LIKE_TEXT_CHOICES).format(
                s=sender.first_name, r=receiver.first_name, p=post
            )
            like_notification = self.create(
                notification_type="like", sent_by=sender, post=post, text=text
            )
            like_notification.sent_to.add(receiver)

            return like_notification

        return notifications.first()

    @atomic
    def create_share_notification(self, sender, post):
        receiver = post.user
        notifications = self.get_queryset().filter(
            notification_type="share", sent_by=sender, sent_to__in=[receiver], post=post
        )

        if not notifications.exists():
            text = random.choice(self.SHARE_TEXT_CHOICES).format(
                s=sender.first_name, r=receiver.first_name, p=post
            )
            share_notification = self.create(
                notification_type="share", sent_by=sender, post=post, text=text
            )
            share_notification.sent_to.add(receiver)

            return share_notification

        return notifications.first()

    @atomic
    def create_report_notification(self, sender, post):
        receiver = post.user
        notifications = self.get_queryset().filter(
            notification_type="report",
            sent_by=sender,
            sent_to__in=[receiver],
            post=post,
        )

        if not notifications.exists():
            text = random.choice(self.REPORT_TEXT_CHOICES).format(
                s=sender.first_name, r=receiver.first_name, p=post
            )
            report_notification = self.create(
                notification_type="report", sent_by=sender, post=post, text=text
            )
            report_notification.sent_to.add(receiver)

            return report_notification

        return notifications.first()

    @atomic
    def create_post_notification(self, receivers, post):
        sender = post.user
        notifications = self.get_queryset().filter(
            notification_type="post", sent_by=sender, post=post
        )

        if not notifications.exists():
            if post.user == sender:
                text = random.choice(self.POST_TEXT_CHOICES).format(
                    s=sender.first_name, p=post
                )

                post_notification = self.create(
                    notification_type="post",
                    sent_by=sender,
                    post=post,
                    text=text,
                )

                for receiver in receivers:
                    post_notification.sent_to.add(receiver)

                return post_notification
            else:
                raise ValidationError("Can't send report notification to a third user.")

        return notifications.first()

    @atomic
    def delete_notification(self, notification_type, sender, post):

        if notification_type == "like":
            notifications = self.get_queryset().filter(
                notification_type="like",
                sent_by=sender,
                post=post,
            )

        elif notification_type == "share":
            notifications = self.get_queryset().filter(
                notification_type="share",
                sent_by=sender,
                post=post,
            )

        elif notification_type == "report":
            notifications = self.get_queryset().filter(
                notification_type="report",
                sent_by=sender,
                post=post,
            )
        else:
            notifications = self.get_queryset().filter(
                notification_type="post", sent_by=sender, post=post
            )

        if notifications.exists():
            notifications.first().delete()
