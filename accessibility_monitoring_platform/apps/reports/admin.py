"""
Admin for reports
"""
from django.contrib import admin

from .models import (
    Report,
    BaseTemplate,
    ReportWrapper,
    ReportVisitsMetrics,
    ReportFeedback,
)

from ..common.admin import ExportCsvMixin


class ReportAdmin(admin.ModelAdmin):
    """Django admin configuration for Report model"""

    readonly_fields = ["created"]
    search_fields = ["case__organisation_name"]
    list_display = ["case", "created"]


class BaseTemplateAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Django admin configuration for BaseTemplate model"""

    readonly_fields = ["created", "version"]
    search_fields = ["name", "content"]
    list_display = ["name", "position", "template_type", "created", "new_page"]
    list_filter = ["template_type"]

    actions = ["export_as_csv"]

    def has_delete_permission(
        self, request, obj=None  # pylint: disable=unused-argument
    ):
        return False


class ReportVisitsMetricsAdmin(admin.ModelAdmin):
    """Django admin configuration for ReportVisitsMetrics model"""

    readonly_fields = ["created"]
    search_fields = ["case", "guid", "fingerprint_codename"]
    list_display = ["created", "case", "fingerprint_codename"]


class ReportFeedbackAdmin(admin.ModelAdmin):
    readonly_fields = ["created"]
    search_fields = ["guid"]
    list_display = ["created", "case", "what_were_you_trying_to_do", "what_went_wrong"]


admin.site.register(Report, ReportAdmin)
admin.site.register(BaseTemplate, BaseTemplateAdmin)
admin.site.register(ReportWrapper)
admin.site.register(ReportVisitsMetrics, ReportVisitsMetricsAdmin)
admin.site.register(ReportFeedback, ReportFeedbackAdmin)
