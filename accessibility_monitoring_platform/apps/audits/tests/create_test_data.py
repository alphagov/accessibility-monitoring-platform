"""Create Wcag and Statement audit data for unit testing"""

from django.utils import timezone

from ...simplified.models import SimplifiedCase
from ..models import (
    AuditOverview,
    StatementAudit,
    StatementCheck,
    StatementCheckResultInitial,
    StatementCheckResultRetest,
    WcagAudit,
    WcagCheckResultInitial,
    WcagCheckResultRetest,
    WcagDefinition,
    WcagPageInitial,
    WcagPageRetest,
)

WCAG_TYPE_AXE_NAME: str = "Axe WCAG"
WCAG_TYPE_MANUAL_NAME: str = "Manual WCAG"
WCAG_TYPE_PDF_NAME: str = "PDF WCAG"


def create_initial_wcag_audit() -> WcagAudit:
    """Create an initial wcag_audit with all types of page and some check results"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    initial_wcag_audit: WcagAudit = WcagAudit.objects.create(
        simplified_case=simplified_case
    )
    AuditOverview.objects.create(
        simplified_case=simplified_case,
    )
    wcag_definitions: list[WcagDefinition] = [
        WcagDefinition.objects.create(
            type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
        ),
        WcagDefinition.objects.create(
            type=WcagDefinition.Type.MANUAL, name=WCAG_TYPE_MANUAL_NAME
        ),
    ]
    wcag_definition_pdf: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.PDF, name=WCAG_TYPE_PDF_NAME
    )
    for page_type in [
        WcagPageInitial.Type.EXTRA,
        WcagPageInitial.Type.HOME,
        WcagPageInitial.Type.CONTACT,
        WcagPageInitial.Type.STATEMENT,
        WcagPageInitial.Type.FORM,
    ]:
        wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.create(
            wcag_audit=initial_wcag_audit, page_type=page_type
        )
        for wcag_definition in wcag_definitions:
            WcagCheckResultInitial.objects.create(
                wcag_audit=initial_wcag_audit,
                wcag_page_initial=wcag_page_initial,
                type=wcag_definition.type,
                wcag_definition=wcag_definition,
            )
    wcag_page_initial_pdf: WcagPageInitial = WcagPageInitial.objects.create(
        wcag_audit=initial_wcag_audit, page_type=WcagPageInitial.Type.PDF
    )
    WcagCheckResultInitial.objects.create(
        wcag_audit=initial_wcag_audit,
        wcag_page_initial=wcag_page_initial_pdf,
        type=wcag_definition_pdf.type,
        wcag_definition=wcag_definition_pdf,
    )
    return initial_wcag_audit


def create_twelve_week_wcag_audit(
    initial_wcag_audit: WcagAudit | None = None,
) -> WcagAudit:
    """Create a twelve week wcag_audit with all types of page and some check results"""
    if initial_wcag_audit is None:
        simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
        AuditOverview.objects.create(
            simplified_case=simplified_case,
        )
    else:
        simplified_case: SimplifiedCase = initial_wcag_audit.simplified_case
    twelve_week_wcag_audit: WcagAudit = WcagAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=WcagAudit.AuditRoundType.TWELVE_WEEK,
    )
    if initial_wcag_audit is not None:
        for wcag_page_initial in initial_wcag_audit.every_wcag_page_initials:
            wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.create(
                wcag_audit=twelve_week_wcag_audit,
                wcag_page_initial=wcag_page_initial,
            )
            for (
                wcag_check_result_initial
            ) in wcag_page_initial.all_wcag_check_result_initials:
                WcagCheckResultRetest.objects.create(
                    wcag_audit=twelve_week_wcag_audit,
                    wcag_page_retest=wcag_page_retest,
                    wcag_check_result_initial=wcag_check_result_initial,
                )
    return twelve_week_wcag_audit


def create_initial_statement_audit(
    simplified_case: SimplifiedCase | None = None,
) -> StatementAudit:
    """Create an initial statement audit with all types of statement checks"""
    if simplified_case is None:
        simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
        AuditOverview.objects.create(
            simplified_case=simplified_case,
        )
    initial_statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case
    )
    for statement_check in StatementCheck.objects.on_date(timezone.now().date()):
        StatementCheckResultInitial.objects.create(
            statement_audit=initial_statement_audit,
            type=statement_check.type,
            statement_check=statement_check,
        )
    StatementCheckResultInitial.objects.create(
        statement_audit=initial_statement_audit,
        public_comment="Custom statement issue",
    )
    return initial_statement_audit


def create_twelve_week_statement_audit(
    initial_statement_audit: StatementAudit | None = None,
) -> StatementAudit:
    """Create a twelve week statement audit with all types of statement checks"""
    if initial_statement_audit is None:
        simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
        AuditOverview.objects.create(
            simplified_case=simplified_case,
        )
    else:
        simplified_case: SimplifiedCase = initial_statement_audit.simplified_case
    twelve_week_statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=simplified_case,
        audit_round_type=StatementAudit.AuditRoundType.TWELVE_WEEK,
    )
    if initial_statement_audit is not None:
        for (
            statement_check_result_initial
        ) in initial_statement_audit.statement_check_results:
            if statement_check_result_initial.statement_check is None:
                StatementCheckResultRetest.objects.create(
                    statement_audit=twelve_week_statement_audit,
                    statement_check_result_initial=statement_check_result_initial,
                    public_comment="Custom statement issue",
                )
            else:
                StatementCheckResultRetest.objects.create(
                    statement_audit=twelve_week_statement_audit,
                    statement_check_result_initial=statement_check_result_initial,
                    type=statement_check_result_initial.type,
                    statement_check=statement_check_result_initial.statement_check,
                )
        StatementCheckResultRetest.objects.create(
            statement_audit=twelve_week_statement_audit,
            type=StatementCheck.Type.TWELVE_WEEK,
            public_comment="Custom statement issue in retest",
        )
    return twelve_week_statement_audit


def create_simplified_case_with_full_audit() -> SimplifiedCase:
    """
    Create simplified case with initial and twelve week wcag and statement audits
    """
    initial_wcag_audit: WcagAudit = create_initial_wcag_audit()
    create_twelve_week_wcag_audit(initial_wcag_audit=initial_wcag_audit)
    initial_statement_audit: StatementAudit = create_initial_statement_audit(
        simplified_case=initial_wcag_audit.simplified_case
    )
    create_twelve_week_statement_audit(initial_statement_audit=initial_statement_audit)
