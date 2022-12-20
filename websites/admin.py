"""Django admin configuration for websites app"""
from django.contrib import admin

from accessibility_monitoring_platform.apps.common.admin import ExportCsvMixin
from .models import Website


class WebsiteAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Django admin configuration for Website model"""

    list_display = [
        "url",
        "type",
        "critical",
        "serious",
        "message",
    ]
    list_filter = ["type", "response_status_code"]
    readonly_fields = [
        "url",
        "type",
        "response_status_code",
        "response_headers",
        "response_content",
        "critical",
        "serious",
        "message",
        "violations",
        "results",
    ]
    search_fields = [
        "url",
        "response_status_code",
        "response_headers",
        "response_content",
    ]
    actions = ["export_as_csv"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("url", "type"),
                    (
                        "response_status_code",
                        "critical",
                        "serious",
                    ),
                    "message",
                    "violations",
                    "results",
                    "response_headers",
                    "response_content",
                )
            },
        ),
    )


admin.site.register(Website, WebsiteAdmin)
