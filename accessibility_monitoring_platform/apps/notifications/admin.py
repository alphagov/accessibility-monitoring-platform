"""
Admin for notifications
"""

from django.contrib import admin

from .models import NotificationSetting, Task


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
        "base_case__case_number",
        "base_case__case_identifier",
        "base_case__organisation_name",
        "description",
    ]
    list_display = [
        "id",
        "date",
        "type",
        "read",
        "base_case",
        "description",
        "user",
    ]
    list_filter = [
        "type",
        "read",
        ("user", admin.RelatedOnlyFieldListFilter),
    ]
    show_facets = admin.ShowFacets.ALWAYS


admin.site.register(NotificationSetting, NotificationSettingAdmin)
admin.site.register(Task, TaskAdmin)
