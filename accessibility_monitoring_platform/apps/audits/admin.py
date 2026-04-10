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
    StatementAudit,
    StatementCheck,
    StatementCheckResult,
    StatementPage,
    WcagAudit,
    WcagCheckResultInitial,
    WcagCheckResultRetest,
    WcagDefinition,
    WcagPageInitial,
    WcagPageRetest,
)


class AuditAdmin(admin.ModelAdmin):
    """Django admin configuration for Audit model"""

    search_fields = [
        "simplified_case__organisation_name",
        "simplified_case__case_identifier",
    ]
    list_display = ["date_of_test", "simplified_case"]
    readonly_fields = ["simplified_case"]
    show_facets = admin.ShowFacets.ALWAYS


class AuditRoundAdmin(admin.ModelAdmin):
    """Django admin configuration for WCAGAudit and StatementAudit models"""

    search_fields = [
        "simplified_case__organisation_name",
        "simplified_case__case_identifier",
    ]
    list_display = [
        "date_of_test",
        "audit_round_type",
        "compliance_state",
        "round",
        "simplified_case",
    ]
    list_filter = ["audit_round_type", "compliance_state", "round", "is_deleted"]
    readonly_fields = ["simplified_case"]
    show_facets = admin.ShowFacets.ALWAYS


class PageAdmin(admin.ModelAdmin):
    """Django admin configuration for Page model"""

    search_fields = [
        "name",
        "url",
        "audit__simplified_case__organisation_name",
        "audit__simplified_case__case_identifier",
    ]
    list_display = ["page_type", "audit", "name", "url"]
    list_filter = ["page_type"]
    readonly_fields = ["audit"]
    show_facets = admin.ShowFacets.ALWAYS


class WcagPageInitialAdmin(admin.ModelAdmin):
    """Django admin configuration for WcagPageInitial model"""

    search_fields = [
        "name",
        "url",
        "first_retest_url",
        "wcag_audit__simplified_case__organisation_name",
        "wcag_audit__simplified_case__case_identifier",
    ]
    list_display = ["page_type", "wcag_audit", "name", "url"]
    list_filter = ["page_type"]
    readonly_fields = ["wcag_audit"]
    show_facets = admin.ShowFacets.ALWAYS


class WcagPageRetestAdmin(admin.ModelAdmin):
    """Django admin configuration for WcagPageInitial model"""

    search_fields = [
        "name",
        "url",
        "wcag_audit__simplified_case__organisation_name",
        "wcag_audit__simplified_case__case_identifier",
    ]
    list_display = ["page_type", "wcag_audit", "name", "url"]
    list_filter = ["page_type"]
    readonly_fields = ["wcag_audit"]
    show_facets = admin.ShowFacets.ALWAYS


class CheckResultAdmin(admin.ModelAdmin):
    """Django admin configuration for CheckResult model"""

    search_fields = [
        "issue_identifier",
        "audit__simplified_case__organisation_name",
        "audit__simplified_case__case_identifier",
        "wcag_definition__name",
        "page__name",
        "page__page_type",
    ]
    list_display = ["issue_identifier", "__str__", "audit", "page"]
    list_filter = ["check_result_state"]
    readonly_fields = ["audit"]
    show_facets = admin.ShowFacets.ALWAYS


class WcagCheckResultInitialAdmin(admin.ModelAdmin):
    """Django admin configuration for WcagCheckResultInitial model"""

    search_fields = [
        "issue_identifier",
        "wcag_page__wcag_audit__simplified_case__organisation_name",
        "wcag_page__wcag_audit__simplified_case__case_identifier",
        "wcag_definition__name",
        "wcag_page__name",
        "wcag_page__page_type",
    ]
    list_display = [
        "issue_identifier",
        "wcag_page__wcag_audit",
        "wcag_page",
        "check_result_state",
        "first_retest_state",
    ]
    list_filter = ["check_result_state", "first_retest_state"]
    readonly_fields = ["wcag_page"]
    show_facets = admin.ShowFacets.ALWAYS


class WcagCheckResultRetestAdmin(admin.ModelAdmin):
    """Django admin configuration for WcagCheckResultRetest model"""

    search_fields = [
        "issue_identifier",
        "wcag_page__wcag_audit__simplified_case__organisation_name",
        "wcag_page__wcag_audit__simplified_case__case_identifier",
        "wcag_definition__name",
        "wcag_page__name",
        "wcag_page__page_type",
    ]
    list_display = [
        "issue_identifier",
        "wcag_page__wcag_audit",
        "wcag_page",
        "retest_state",
    ]
    list_filter = ["retest_state"]
    readonly_fields = ["wcag_page"]
    show_facets = admin.ShowFacets.ALWAYS


class CheckResultNotesHistoryAdmin(admin.ModelAdmin):
    search_fields = [
        "check_result__issue_identifier",
        "check_result__audit__simplified_case__organisation_name",
        "check_result__audit__simplified_case__case_identifier",
        "check_result__wcag_definition__name",
        "check_result__page__name",
        "check_result__page__page_type",
    ]
    list_display = ["check_result", "created_by", "created"]
    list_filter = ["created_by"]
    readonly_fields = ["check_result", "created"]
    show_facets = admin.ShowFacets.ALWAYS


class CheckResultRetestNotesHistoryAdmin(admin.ModelAdmin):
    search_fields = [
        "check_result__issue_identifier",
        "check_result__audit__simplified_case__organisation_name",
        "check_result__audit__simplified_case__case_identifier",
        "check_result__wcag_definition__name",
        "check_result__page__name",
        "check_result__page__page_type",
    ]
    list_display = ["check_result", "created_by", "retest_state", "created"]
    list_filter = ["created_by", "retest_state"]
    readonly_fields = ["check_result", "created"]
    show_facets = admin.ShowFacets.ALWAYS


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
    show_facets = admin.ShowFacets.ALWAYS


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
    actions = ["export_as_csv"]
    show_facets = admin.ShowFacets.ALWAYS


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
    show_facets = admin.ShowFacets.ALWAYS


class RetestAdmin(admin.ModelAdmin):
    """Django admin configuration for Retest model"""

    search_fields = [
        "simplified_case__organisation_name",
        "simplified_case__case_identifier",
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
    show_facets = admin.ShowFacets.ALWAYS


class RetestPageAdmin(admin.ModelAdmin):
    """Django admin configuration for RetestPage model"""

    search_fields = [
        "page__name",
        "page__url",
        "retest__simplified_case__organisation_name",
    ]
    list_display = ["page", "retest", "missing_date"]
    list_filter = ["page__page_type"]
    show_facets = admin.ShowFacets.ALWAYS


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
    show_facets = admin.ShowFacets.ALWAYS


class StatementPageAdmin(admin.ModelAdmin):
    """Django admin configuration for StatementPage model"""

    search_fields = ["audit__simplified_case__case_identifier", "url", "backup_url"]
    list_display = ["id", "url", "backup_url", "added_stage", "is_deleted", "created"]
    list_filter = ["added_stage", "is_deleted"]
    readonly_fields = ["audit", "statement_audit"]
    show_facets = admin.ShowFacets.ALWAYS


class RetestStatementCheckResultAdmin(admin.ModelAdmin):
    """Django admin configuration for RetestStatementCheckResult model"""

    search_fields = [
        "issue_identifier",
        "statement_audit__simplified_case__case_identifier",
        "statement_audit__simplified_case__organisation_name",
        "statement_check__label",
        "comment",
    ]
    list_display = [
        "issue_identifier",
        "statement_audit",
        "type",
        "check_result_state",
        "is_deleted",
        "statement_check",
    ]
    list_filter = ["check_result_state", "is_deleted"]
    readonly_fields = ["retest", "statement_audit", "statement_check"]
    show_facets = admin.ShowFacets.ALWAYS


admin.site.register(Audit, AuditAdmin)
admin.site.register(WcagAudit, AuditRoundAdmin)
admin.site.register(StatementAudit, AuditRoundAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(WcagPageInitial, WcagPageInitialAdmin)
admin.site.register(WcagPageRetest, WcagPageRetestAdmin)
admin.site.register(CheckResult, CheckResultAdmin)
admin.site.register(WcagCheckResultInitial, WcagCheckResultInitialAdmin)
admin.site.register(WcagCheckResultRetest, WcagCheckResultRetestAdmin)
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
