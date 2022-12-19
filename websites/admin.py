"""Django admin configuration for websites app"""
from django.contrib import admin

from accessibility_monitoring_platform.apps.common.admin import ExportCsvMixin
from .models import Website


class WebsiteAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Django admin configuration for Website model"""

    list_display = ["url", "response_status_code", "response_type", "response_content"]
    list_filter = ["response_type", "response_status_code"]
    readonly_fields = [
        "url",
        "response_status_code",
        "response_headers",
        "response_content",
    ]
    search_fields = [
        "url",
        "response_status_code",
        "response_headers",
        "response_content",
    ]
    actions = ["export_as_csv"]


admin.site.register(Website, WebsiteAdmin)
