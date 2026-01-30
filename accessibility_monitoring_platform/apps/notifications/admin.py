"""
Admin for notifications
"""

from django.contrib import admin

from .models import CaseTask, NotificationSetting, Task


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


class CaseTaskAdmin(admin.ModelAdmin):
    """Django admin configuration for CaseTask model"""

    search_fields = [
        "base_case__case_number",
        "base_case__case_identifier",
        "base_case__organisation_name",
        "text",
    ]
    list_display = [
        "id",
        "due_date",
        "type",
        "is_complete",
        "base_case",
        "text",
        "created_by",
    ]
    list_filter = [
        "type",
        "is_complete",
        ("created_by", admin.RelatedOnlyFieldListFilter),
    ]
    show_facets = admin.ShowFacets.ALWAYS
    readonly_fields = ["created", "updated"]
    filter_horizontal = ("recipients",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("due_date", "type"),
                    ("created_by"),
                    ("text",),
                    ("recipients",),
                    ("completed_by"),
                    ("is_complete"),
                    ("created", "updated"),
                )
            },
        ),
    )


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
admin.site.register(CaseTask, CaseTaskAdmin)
admin.site.register(Task, TaskAdmin)
