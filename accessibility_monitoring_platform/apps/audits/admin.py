"""
Admin for checks (called tests by the users)
"""

from django.contrib import admin

from ..common.admin import ExportCsvMixin
from .models import (
    Audit,
    Page,
    CheckResult,
    WcagDefinition,
    StatementCheck,
    StatementCheckResult,
)


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


class StatementCheckAdmin(admin.ModelAdmin):
    """Django admin configuration for StatementCheck model"""

    search_fields = ["label", "success_criteria", "report_text"]
    list_display = ["label", "type", "position", "is_deleted"]
    list_filter = ["type", "is_deleted"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("type", "position", "is_deleted"),
                    ("label",),
                    ("success_criteria",),
                    ("report_text",),
                )
            },
        ),
    )


class StatementCheckResultAdmin(admin.ModelAdmin):
    """Django admin configuration for StatementCheck model"""

    search_fields = [
        "audit__case__organisation_name",
        "statement_check__label",
        "statement_check__success_criteria",
        "statement_check__report_text",
    ]
    list_display = ["statement_check", "audit", "is_deleted"]
    list_filter = ["is_deleted", "check_result_state", "retest_state"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("type", "is_deleted"),
                    ("audit",),
                    ("statement_check",),
                    ("check_result_state",),
                    ("report_comment",),
                    ("retest_state",),
                    ("retest_comment",),
                )
            },
        ),
    )


admin.site.register(Audit, AuditAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(CheckResult, CheckResultAdmin)
admin.site.register(WcagDefinition, WcagDefinitionAdmin)
admin.site.register(StatementCheck, StatementCheckAdmin)
admin.site.register(StatementCheckResult, StatementCheckResultAdmin)
