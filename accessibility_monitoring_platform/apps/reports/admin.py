"""
Admin for reports
"""
from django.contrib import admin

from .models import (
    Report,
    BaseTemplate,
    Section,
    TableRow,
    ReportWrapper,
    ReportVisitsMetrics,
    ReportFeedback,
)

from ..common.admin import ExportCsvMixin


class SectionInline(admin.TabularInline):
    model = Section
    fields = ["name", "template_type", "content"]
    readonly_fields = ["name", "template_type", "content"]
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj):  # pylint: disable=unused-argument
        return False


class ReportAdmin(admin.ModelAdmin):
    """Django admin configuration for Report model"""

    readonly_fields = ["created"]
    search_fields = ["case__organisation_name"]
    list_display = ["case", "created"]
    inlines = [SectionInline]


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


class TableRowInline(admin.TabularInline):
    model = TableRow
    fields = ["cell_content_1", "cell_content_2"]
    readonly_fields = ["cell_content_1", "cell_content_2"]
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj):  # pylint: disable=unused-argument
        return False


class SectionAdmin(admin.ModelAdmin):
    """Django admin configuration for Section model"""

    readonly_fields = ["created", "version"]
    search_fields = ["name", "content"]
    list_display = ["report", "name", "position", "created"]
    inlines = [TableRowInline]


class TableRowAdmin(admin.ModelAdmin):
    """Django admin configuration for TableRow model"""

    readonly_fields = ["created", "version"]
    search_fields = ["cell_content_1", "cell_content_2"]
    list_display = ["section", "row_number", "created", "is_deleted"]
    list_filter = ["is_deleted"]


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
admin.site.register(Section, SectionAdmin)
admin.site.register(TableRow, TableRowAdmin)
admin.site.register(ReportWrapper)
admin.site.register(ReportVisitsMetrics, ReportVisitsMetricsAdmin)
admin.site.register(ReportFeedback, ReportFeedbackAdmin)
