"""
Admin for reports
"""
from django.contrib import admin

from ..common.admin import ExportCsvMixin
from .models import Report, ReportVisitsMetrics, ReportWrapper


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


admin.site.register(Report, ReportAdmin)
admin.site.register(ReportWrapper)
admin.site.register(ReportVisitsMetrics, ReportVisitsMetricsAdmin)
