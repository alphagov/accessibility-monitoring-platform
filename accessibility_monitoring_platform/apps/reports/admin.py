"""
Admin for reports
"""
from django.contrib import admin

from .models import (
    Report,
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
admin.site.register(ReportWrapper)
admin.site.register(ReportVisitsMetrics, ReportVisitsMetricsAdmin)
admin.site.register(ReportFeedback, ReportFeedbackAdmin)
