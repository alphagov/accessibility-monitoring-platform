"""
Admin for checks (called tests by the users)
"""

from django.contrib import admin

from ..common.admin import ExportCsvMixin
from .models import (
    Audit,
    CheckResult,
    CheckResultNotesHistory,
    CheckResultRetestNotesHistory,
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

    search_fields = [
        "simplified_case__organisation_name",
        "simplified_case__case_number",
    ]
    list_display = ["date_of_test", "simplified_case"]
    readonly_fields = ["simplified_case"]


class PageAdmin(admin.ModelAdmin):
    """Django admin configuration for Page model"""

    search_fields = [
        "name",
        "url",
        "audit__simplified_case__organisation_name",
        "audit__simplified_case__case_number",
    ]
    list_display = ["page_type", "audit", "name", "url"]
    list_filter = ["page_type"]


class CheckResultAdmin(admin.ModelAdmin):
    """Django admin configuration for CheckResult model"""

    search_fields = [
        "issue_identifier",
        "audit__simplified_case__organisation_name",
        "audit__simplified_case__case_number",
        "wcag_definition__name",
        "page__name",
        "page__page_type",
    ]
    list_display = ["issue_identifier", "__str__", "audit", "page"]
    list_filter = ["check_result_state"]
    readonly_fields = ["audit"]


class CheckResultNotesHistoryAdmin(admin.ModelAdmin):
    search_fields = [
        "check_result__issue_identifier",
        "check_result__audit__simplified_case__organisation_name",
        "check_result__audit__simplified_case__case_number",
        "check_result__wcag_definition__name",
        "check_result__page__name",
        "check_result__page__page_type",
    ]
    list_display = ["check_result", "created_by", "created"]
    list_filter = ["created_by"]
    readonly_fields = ["check_result", "created"]


class CheckResultRetestNotesHistoryAdmin(admin.ModelAdmin):
    search_fields = [
        "check_result__issue_identifier",
        "check_result__audit__simplified_case__organisation_name",
        "check_result__audit__simplified_case__case_number",
        "check_result__wcag_definition__name",
        "check_result__page__name",
        "check_result__page__page_type",
    ]
    list_display = ["check_result", "created_by", "retest_state", "created"]
    list_filter = ["created_by", "retest_state"]
    readonly_fields = ["check_result", "created"]


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


class StatementCheckAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Django admin configuration for StatementCheck model"""

    search_fields = ["label", "success_criteria", "report_text"]
    list_display = [
        "issue_number",
        "label",
        "type",
        "position",
        "date_start",
        "date_end",
    ]
    list_filter = ["type"]
    actions = ["export_as_csv"]
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
        "issue_identifier",
        "audit__simplified_case__organisation_name",
        "statement_check__label",
        "statement_check__success_criteria",
        "statement_check__report_text",
    ]
    list_display = ["issue_identifier", "statement_check", "audit", "is_deleted"]
    list_filter = ["is_deleted", "check_result_state", "retest_state", "type"]
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
                    ("auditor_notes",),
                )
            },
        ),
    )
    readonly_fields = ["audit"]


class RetestAdmin(admin.ModelAdmin):
    """Django admin configuration for Retest model"""

    search_fields = [
        "simplified_case__organisation_name",
        "simplified_case__case_number",
        "retest_notes",
        "compliance_notes",
    ]
    list_display = [
        "__str__",
        "simplified_case",
        "retest_compliance_state",
        "date_of_retest",
        "is_deleted",
    ]
    ordering = ["-id"]
    list_filter = ["retest_compliance_state", "is_deleted"]


class RetestPageAdmin(admin.ModelAdmin):
    """Django admin configuration for RetestPage model"""

    search_fields = [
        "page__name",
        "page__url",
        "retest__simplified_case__organisation_name",
    ]
    list_display = ["page", "retest", "missing_date"]
    list_filter = ["page__page_type"]


class RetestCheckResultAdmin(admin.ModelAdmin):
    """Django admin configuration for RetestCheckResult model"""

    search_fields = [
        "issue_identifier",
        "check_result__wcag_definition__name",
        "retest__simplified_case__organisation_name",
        "retest_page__page__name",
        "retest_page__page__url",
    ]
    list_display = [
        "issue_identifier",
        "check_result",
        "retest",
        "retest_page",
        "retest_state",
    ]
    list_filter = ["retest_state"]
    readonly_fields = ["check_result", "retest_page", "retest"]


class StatementPageAdmin(admin.ModelAdmin):
    """Django admin configuration for StatementPage model"""

    search_fields = ["audit__simplified_case__case_number", "url", "backup_url"]
    list_display = ["id", "url", "backup_url", "added_stage", "is_deleted", "created"]
    list_filter = ["added_stage", "is_deleted"]
    readonly_fields = ["audit"]


class RetestStatementCheckResultAdmin(admin.ModelAdmin):
    """Django admin configuration for RetestStatementCheckResult model"""

    search_fields = [
        "issue_identifier",
        "retest__simplified_case__case_number",
        "retest__simplified_case__organisation_name",
        "statement_check__label",
        "comment",
    ]
    list_display = [
        "issue_identifier",
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
admin.site.register(CheckResultNotesHistory, CheckResultNotesHistoryAdmin)
admin.site.register(CheckResultRetestNotesHistory, CheckResultRetestNotesHistoryAdmin)
admin.site.register(WcagDefinition, WcagDefinitionAdmin)
admin.site.register(StatementCheck, StatementCheckAdmin)
admin.site.register(StatementCheckResult, StatementCheckResultAdmin)
admin.site.register(Retest, RetestAdmin)
admin.site.register(RetestPage, RetestPageAdmin)
admin.site.register(RetestCheckResult, RetestCheckResultAdmin)
admin.site.register(StatementPage, StatementPageAdmin)
admin.site.register(RetestStatementCheckResult, RetestStatementCheckResultAdmin)
