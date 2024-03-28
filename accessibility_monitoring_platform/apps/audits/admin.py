"""
Admin for checks (called tests by the users)
"""

from django.contrib import admin

from ..common.admin import ExportCsvMixin
from .models import (
    Audit,
    CheckResult,
    Page,
    Retest,
    RetestCheckResult,
    RetestPage,
    RetestStatementCheckResult,
    StatementCheck,
    StatementCheckResult,
    StatementPage,
    WcagDefinition,
)


class AuditAdmin(admin.ModelAdmin):
    """Django admin configuration for Audit model"""

    search_fields = ["case__organisation_name", "case__id"]
    list_display = ["date_of_test", "case"]
    readonly_fields = ["case"]


class PageAdmin(admin.ModelAdmin):
    """Django admin configuration for Page model"""

    search_fields = ["name", "url", "audit__case__organisation_name", "audit__case__id"]
    list_display = ["page_type", "audit", "name", "url"]
    list_filter = ["page_type"]


class CheckResultAdmin(admin.ModelAdmin):
    """Django admin configuration for CheckResult model"""

    search_fields = [
        "audit__case__organisation_name",
        "audit__case__id",
        "wcag_definition__name",
        "page__name",
    ]
    list_display = ["wcag_definition", "audit", "page"]


class WcagDefinitionAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Django admin configuration for WcagDefinition model"""

    search_fields = ["name", "description"]
    list_display = [
        "id",
        "type",
        "name",
        "description",
        "date_start",
        "date_end",
    ]
    list_filter = ["type"]
    actions = ["export_as_csv"]


class StatementCheckAdmin(admin.ModelAdmin):
    """Django admin configuration for StatementCheck model"""

    search_fields = ["label", "success_criteria", "report_text"]
    list_display = ["label", "type", "position", "date_start", "date_end"]
    list_filter = ["type"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("type", "position"),
                    ("date_start", "date_end"),
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


class RetestAdmin(admin.ModelAdmin):
    """Django admin configuration for Retest model"""

    search_fields = [
        "case__organisation_name",
        "case__id",
        "retest_notes",
        "compliance_notes",
    ]
    list_display = ["__str__", "case", "retest_compliance_state", "is_deleted"]
    list_filter = ["retest_compliance_state", "is_deleted"]


class RetestPageAdmin(admin.ModelAdmin):
    """Django admin configuration for RetestPage model"""

    search_fields = ["page__name", "page__url", "retest__case__organisation_name"]
    list_display = ["page", "retest", "missing_date"]
    list_filter = ["page__page_type"]


class RetestCheckResultAdmin(admin.ModelAdmin):
    """Django admin configuration for RetestCheckResult model"""

    search_fields = [
        "check_result__wcag_definition__name",
        "retest__case__organisation_name",
        "retest_page__page__name",
        "retest_page__page__url",
    ]
    list_display = [
        "check_result",
        "retest",
        "retest_page",
        "retest_state",
    ]
    list_filter = ["retest_state"]
    readonly_fields = ["check_result", "retest_page", "retest"]


class StatementPageAdmin(admin.ModelAdmin):
    """Django admin configuration for StatementPage model"""

    search_fields = ["audit__case__id", "url", "backup_url"]
    list_display = ["id", "url", "backup_url", "added_stage", "is_deleted", "created"]
    list_filter = ["added_stage", "is_deleted"]
    readonly_fields = ["audit"]


class RetestStatementCheckResultAdmin(admin.ModelAdmin):
    """Django admin configuration for RetestStatementCheckResult model"""

    search_fields = [
        "retest__case__id",
        "retest__case__organisation_name",
        "statement_check__label",
        "comment",
    ]
    list_display = [
        "id",
        "retest",
        "type",
        "check_result_state",
        "is_deleted",
        "statement_check",
    ]
    list_filter = ["check_result_state", "is_deleted"]
    readonly_fields = ["retest", "statement_check"]


admin.site.register(Audit, AuditAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(CheckResult, CheckResultAdmin)
admin.site.register(WcagDefinition, WcagDefinitionAdmin)
admin.site.register(StatementCheck, StatementCheckAdmin)
admin.site.register(StatementCheckResult, StatementCheckResultAdmin)
admin.site.register(Retest, RetestAdmin)
admin.site.register(RetestPage, RetestPageAdmin)
admin.site.register(RetestCheckResult, RetestCheckResultAdmin)
admin.site.register(StatementPage, StatementPageAdmin)
admin.site.register(RetestStatementCheckResult, RetestStatementCheckResultAdmin)
