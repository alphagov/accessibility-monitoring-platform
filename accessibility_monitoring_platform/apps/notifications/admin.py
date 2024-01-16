"""
Admin for notifications
"""
from django.contrib import admin

from .models import Notification, NotificationSetting


class NotificationsAdmin(admin.ModelAdmin):
    """Django admin configuration for Notification model"""

    readonly_fields = ["created_date"]
    search_fields = [
        "user__email",
        "body",
        "path",
        "list_description",
    ]
    list_display = [
        "user",
        "body",
        "created_date",
        "read",
        "path",
        "list_description",
    ]


class NotificationsSettingsAdmin(admin.ModelAdmin):
    """Django admin configuration for NotificationSettings model"""

    search_fields = [
        "user__email",
        "email_notifications_enabled",
    ]
    list_display = [
        "user",
        "email_notifications_enabled",
    ]


admin.site.register(Notification, NotificationsAdmin)
admin.site.register(NotificationSetting, NotificationsSettingsAdmin)
