from django.contrib import admin

from .models import UserAccount, Post, Connection, Notification


class UserAccountAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "username", "created_at"]


class PostAdmin(admin.ModelAdmin):
    list_display = ["user", "username", "created_at"]


class NotificationAdmin(admin.ModelAdmin):
    list_display = ["sent_by", "notification_type", "created_at"]


admin.site.register(UserAccount, UserAccountAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Connection)
admin.site.register(Notification, NotificationAdmin)