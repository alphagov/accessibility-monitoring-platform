"""
Admin for reports
"""
from django.contrib import admin

from .models import Report, BaseTemplate

from ..common.admin import ExportCsvMixin


class ReportAdmin(admin.ModelAdmin):
    """Django admin configuration for Report model"""

    readonly_fields = ["created"]
    search_fields = ["case__organisation_name"]
    list_display = ["case", "created"]
    list_filter = ["ready_for_qa"]


class BaseTemplateAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Django admin configuration for BaseTemplate model"""

    readonly_fields = ["created", "version"]
    search_fields = ["name", "content"]
    list_display = ["name", "position", "created"]
    list_filter = ["name"]

    actions = ["export_as_csv"]

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Report, ReportAdmin)
admin.site.register(BaseTemplate, BaseTemplateAdmin)
