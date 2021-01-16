from django.db import models
from django.contrib.auth.models import User
from django.db.models.fields import related
from django.db.models.lookups import Regex
from django_resized import ResizedImageField
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

from datetime import date

from .managers import ConnectionManager, NotificationManager


def get_dp_path(instance, filename):
    return f"media/user/{slugify(instance.username)}/{filename}"


def get_media_path(instance, filename):
    return f"media/{slugify(instance.user.username)}/{filename}"


class TrackingModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserAccount(TrackingModel):
    user = models.OneToOneField(User, related_name="user", on_delete=models.CASCADE)

    first_name = models.CharField(
        max_length=30,
        validators=[
            RegexValidator(
                r"^[A-Z]?[a-z]*$",
                message="First name is compulsory and should contain only letters, and no spaces",
            )
        ],
        blank=False,
        null=False,
    )

    last_name = models.CharField(
        max_length=30,
        validators=[
            RegexValidator(
                r"^[A-Z]?[a-z]*$",
                message="Last name should contain only letters, and no spaces",
            )
        ],
        blank=True,
        null=True,
        default="",
    )

    phone = models.CharField(
        max_length=13, validators=[RegexValidator(r"^(\+91|0|91)?[6789]([0-9]{9})$")]
    )

    display_picture = ResizedImageField(
        upload_to=get_dp_path,
        size=[300, 300],
        quality=100,
        blank=True,
    )

    date_of_birth = models.DateField(blank=False, null=False)

    is_premium = models.BooleanField(default=False)

    profile_summary = models.TextField(max_length=300, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def username(self):  # username getter
        return self.user.username

    def clean(self):
        today = date.today()

        if (today - self.date_of_birth).days // 365 < 18:
            raise ValidationError(_("User can't be below the age of 18"))

    class Meta:
        verbose_name = "User Account"


class Post(TrackingModel):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)

    text = models.TextField(max_length=300, blank=True, null=True)

    media = models.FileField(upload_to=get_media_path, null=True)

    likes = models.PositiveIntegerField(default=0)

    reports = models.PositiveIntegerField(default=0)

    @property
    def username(self):
        return self.user.username

    def __str__(self):
        return f"[{self.user.first_name}]-{self.text}"


class Connection(TrackingModel):
    id = models.AutoField(primary_key=True)

    # can't have more than two users
    users = models.ManyToManyField(UserAccount, related_name="connection_between")

    # should have one of the users only
    sent_by = models.ForeignKey(UserAccount, on_delete=models.CASCADE, db_index=True)

    accepted = models.BooleanField(default=False)

    objects = ConnectionManager()

    def __str__(self):
        return f"[{self.users.first()}] -> [{self.users.last()}]"


NOTIFICATION_TYPE_CHOICES = (
    ("like", "like"),  # sent to a specific user whose post is liked
    ("share", "share"),  # sent to a specific user whose post is shared
    ("post", "post"),  # sent to all the users in connection of the user who is posting
    ("report", "report"),  # sent to  the specific user whose account has been reported
)


class Notification(TrackingModel):
    id = models.AutoField(primary_key=True)

    sent_by = models.ForeignKey(UserAccount, on_delete=models.CASCADE, db_index=True)

    sent_to = models.ManyToManyField(
        UserAccount,
        related_name="notification_to",
    )

    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    notification_type = models.CharField(
        max_length=10, choices=NOTIFICATION_TYPE_CHOICES, blank=False, null=False
    )

    url = models.CharField(max_length=100, blank=True, null=True)

    text = models.TextField(max_length=200, blank=True, null=True)

    objects = NotificationManager()

    def __str__(self):
        return f"{self.id} -> {self.sent_by.first_name}"