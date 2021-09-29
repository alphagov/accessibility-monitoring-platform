"""
Admin for notifications
"""
from django.contrib import admin
from .models import Notifications, NotificationsSettings


class NotificationsAdmin(admin.ModelAdmin):
    """Django admin configuration for Notifications model"""

    readonly_fields = ["created_date"]
    search_fields = [
        "user__email",
        "body",
        "endpoint",
        "list_description",
    ]
    list_display = [
        "user",
        "body",
        "created_date",
        "read",
        "endpoint",
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


admin.site.register(Notifications, NotificationsAdmin)
admin.site.register(NotificationsSettings, NotificationsSettingsAdmin)
