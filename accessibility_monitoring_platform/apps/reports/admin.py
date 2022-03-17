"""
Admin for reports
"""
from django.contrib import admin

from .models import Report, BaseTemplate, Section, TableRow

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
    list_display = ["name", "position", "template_type", "created"]
    list_filter = ["template_type"]

    actions = ["export_as_csv"]

    def has_delete_permission(
        self, request, obj=None
    ):  # pylint: disable=unused-argument
        return False


class SectionAdmin(admin.ModelAdmin):
    """Django admin configuration for Section model"""

    readonly_fields = ["created", "version"]
    search_fields = ["name", "content"]
    list_display = ["report", "name", "position", "created"]


class TableRowAdmin(admin.ModelAdmin):
    """Django admin configuration for TableRow model"""

    readonly_fields = ["created", "version"]
    search_fields = ["cell_content_1", "cell_content_2"]
    list_display = ["section", "row_number", "created"]


admin.site.register(Report, ReportAdmin)
admin.site.register(BaseTemplate, BaseTemplateAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(TableRow, TableRowAdmin)
