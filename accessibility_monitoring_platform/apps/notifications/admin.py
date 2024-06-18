"""
Admin for notifications
"""

from django.contrib import admin

from .models import Notification, NotificationSetting, Task


class NotificationAdmin(admin.ModelAdmin):
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


class NotificationSettingAdmin(admin.ModelAdmin):
    """Django admin configuration for NotificationSetting model"""

    search_fields = [
        "user__email",
        "email_notifications_enabled",
    ]
    list_display = [
        "user",
        "email_notifications_enabled",
    ]


class TaskAdmin(admin.ModelAdmin):
    """Django admin configuration for Task model"""

    search_fields = [
        "case__organisation_name",
        "description",
    ]
    list_display = [
        "id",
        "date",
        "type",
        "read",
        "case",
        "description",
        "user",
    ]
    list_filter = [
        "type",
        "read",
        ("user", admin.RelatedOnlyFieldListFilter),
    ]
    show_facets = admin.ShowFacets.ALWAYS


admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationSetting, NotificationSettingAdmin)
admin.site.register(Task, TaskAdmin)
