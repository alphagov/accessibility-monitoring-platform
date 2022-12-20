"""Django admin configuration for websites app"""
from django.contrib import admin

from accessibility_monitoring_platform.apps.common.admin import ExportCsvMixin
from .models import Website


class WebsiteAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Django admin configuration for Website model"""

    list_display = [
        "url",
        "axe_core_critical_count",
        "axe_core_serious_count",
        "axe_core_message",
    ]
    list_filter = ["response_type", "response_status_code"]
    readonly_fields = [
        "url",
        "response_status_code",
        "response_headers",
        "response_content",
        "axe_core_critical_count",
        "axe_core_serious_count",
        "axe_core_message",
        "axe_core_violations",
        "axe_core_results",
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
                    "url",
                    (
                        "response_status_code",
                        "axe_core_critical_count",
                        "axe_core_serious_count",
                    ),
                    "axe_core_message",
                    "axe_core_violations",
                    "axe_core_results",
                    "response_headers",
                    "response_content",
                )
            },
        ),
    )


admin.site.register(Website, WebsiteAdmin)
