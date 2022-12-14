"""
Admin for checks (called tests by the users)
"""

from django.contrib import admin

from ..common.admin import ExportCsvMixin
from .models import Audit, Page, CheckResult, WcagDefinition


class AuditAdmin(admin.ModelAdmin):
    """Django admin configuration for Audit model"""

    search_fields = ["case__organisation_name"]
    list_display = ["date_of_test", "case"]


class PageAdmin(admin.ModelAdmin):
    """Django admin configuration for Page model"""

    search_fields = ["name", "url", "audit__case_organisation_name"]
    list_display = ["page_type", "audit", "name", "url"]
    list_filter = ["page_type"]


class CheckResultAdmin(admin.ModelAdmin):
    """Django admin configuration for CheckResult model"""

    search_fields = [
        "wcag_definition__name",
        "audit__description",
        "page__name",
        "page__type",
        "page__url",
    ]
    list_display = ["wcag_definition", "audit", "page"]


class WcagDefinitionAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Django admin configuration for WcagDefinition model"""

    search_fields = ["name", "description"]
    list_display = ["id", "type", "name", "description"]
    list_filter = ["type"]
    actions = ["export_as_csv"]


admin.site.register(Audit, AuditAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(CheckResult, CheckResultAdmin)
admin.site.register(WcagDefinition, WcagDefinitionAdmin)
