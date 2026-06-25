"""
Test utility functions of reports app
"""

import pytest

from ...audits.models import (
    AuditOverview,
    StatementAudit,
    WcagAudit,
    WcagCheckResultInitial,
    WcagCheckResultRetest,
    WcagDefinition,
    WcagPageInitial,
)
from ...audits.tests.create_test_data import (
    create_simplified_case_with_initial_and_12_week_audits,
)
from ...simplified.models import SimplifiedCase
from ..models import Report
from ..utils import (
    IssueTable,
    TableRow,
    build_issue_table_rows,
    build_issues_tables,
    build_report_context,
)

NUMBER_OF_TOP_LEVEL_BASE_TEMPLATES: int = 9
HOME_PAGE_NAME: str = "Home name"
PDF_PAGE_NAME: str = "PDF name"
HOME_PAGE_URL: str = "https://example.com/home"
PDF_PAGE_URL: str = "https://example.com/pdf"
CHECK_RESULT_NOTES: str = "Check results note <span>including HTML</span>"
CHECK_RESULT_RETEST_NOTES: str = "Check results retest note <span>including HTML</span>"


@pytest.mark.django_db
def test_build_issue_table_rows():
    """Test issue table row created for failed check"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    wcag_audit: WcagAudit = WcagAudit.objects.create(simplified_case=simplified_case)
    wcag_page_initial: WcagPageInitial = WcagPageInitial.objects.create(
        wcag_audit=wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
        name=HOME_PAGE_NAME,
        url=HOME_PAGE_URL,
    )
    wcag_definition: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.AXE
    ).first()
    WcagCheckResultInitial.objects.create(
        wcag_audit=wcag_audit,
        wcag_page_initial=wcag_page_initial,
        wcag_definition=wcag_definition,
        check_result_state=WcagCheckResultInitial.Result.ERROR,
        notes=CHECK_RESULT_NOTES,
    )
    used_wcag_definitions: set[WcagDefinition] = set()

    table_rows: list[TableRow] = build_issue_table_rows(
        check_results=wcag_page_initial.failed_wcag_check_result_initials,
        used_wcag_definitions=used_wcag_definitions,
    )

    assert len(table_rows) == 1

    assert wcag_definition.name in table_rows[0].cell_content_1
    assert CHECK_RESULT_NOTES in table_rows[0].cell_content_2


@pytest.mark.django_db
def test_twelve_week_build_issue_table_rows():
    """Test issue table row created for 12-week retest failed check"""
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    wcag_audit: WcagAudit = simplified_case.audit_overview.first_twelve_week_wcag_audit
    wcag_check_result_retest: WcagCheckResultRetest = (
        WcagCheckResultRetest.objects.filter(wcag_audit=wcag_audit).first()
    )
    wcag_check_result_retest.retest_state = WcagCheckResultRetest.RetestResult.NOT_FIXED
    wcag_check_result_retest.notes = CHECK_RESULT_RETEST_NOTES
    wcag_check_result_retest.save()
    wcag_check_result_initial: WcagCheckResultRetest = (
        wcag_check_result_retest.wcag_check_result_initial
    )
    wcag_check_result_initial.check_result_state = WcagCheckResultInitial.Result.ERROR
    wcag_check_result_initial.notes = CHECK_RESULT_NOTES
    wcag_check_result_initial.save()
    wcag_page_initial: WcagPageInitial = (
        wcag_check_result_retest.wcag_check_result_initial.wcag_page_initial
    )
    wcag_page_initial.name = HOME_PAGE_NAME
    wcag_page_initial.url = HOME_PAGE_URL
    wcag_page_initial.save()
    used_wcag_definitions: set[WcagDefinition] = set()

    table_rows: list[TableRow] = build_issue_table_rows(
        check_results=wcag_page_initial.failed_wcag_check_result_initials,
        used_wcag_definitions=used_wcag_definitions,
        use_retest_notes=True,
    )

    assert len(table_rows) == 1

    assert (
        wcag_check_result_initial.wcag_definition.name in table_rows[0].cell_content_1
    )
    assert CHECK_RESULT_RETEST_NOTES in table_rows[0].cell_content_2


@pytest.mark.django_db
def test_report_boilerplate_shown_only_once():
    """
    Test report contains WCAG definition's boilerplate text
    only the first time that definition appears.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    wcag_audit: WcagAudit = WcagAudit.objects.create(simplified_case=simplified_case)
    first_page: WcagPageInitial = WcagPageInitial.objects.create(
        wcag_audit=wcag_audit,
        name=HOME_PAGE_NAME,
        page_type=WcagPageInitial.Type.HOME,
        url=HOME_PAGE_URL,
    )
    second_page: WcagPageInitial = WcagPageInitial.objects.create(
        wcag_audit=wcag_audit,
        name=PDF_PAGE_NAME,
        page_type=WcagPageInitial.Type.PDF,
        url=PDF_PAGE_URL,
    )
    Report.objects.create(base_case=simplified_case)
    wcag_definition: WcagDefinition = WcagDefinition.objects.filter(
        type=WcagDefinition.Type.PDF
    ).first()
    WcagCheckResultInitial.objects.create(
        wcag_audit=wcag_audit,
        wcag_page_initial=first_page,
        wcag_definition=wcag_definition,
        check_result_state=WcagCheckResultInitial.Result.ERROR,
    )
    WcagCheckResultInitial.objects.create(
        wcag_audit=wcag_audit,
        wcag_page_initial=second_page,
        wcag_definition=wcag_definition,
        check_result_state=WcagCheckResultInitial.Result.ERROR,
    )

    issues_tables: list[IssueTable] = build_issues_tables(
        pages=wcag_audit.testable_wcag_page_initials
    )

    table_rows: list[TableRow] = []
    for issues_table in issues_tables:
        for table_row in issues_table.rows:
            if wcag_definition.name in table_row.cell_content_1:
                table_rows.append(table_row)

    assert len(table_rows) == 2

    assert wcag_definition.name in table_rows[0].cell_content_1
    assert wcag_definition.report_boilerplate in table_rows[0].cell_content_1
    assert wcag_definition.name in table_rows[1].cell_content_1
    assert wcag_definition.report_boilerplate not in table_rows[1].cell_content_1


@pytest.mark.django_db
def test_generate_report_content_issues_tables():
    """Test report contains issues tables for each page"""
    simplified_case: SimplifiedCase = (
        create_simplified_case_with_initial_and_12_week_audits()
    )
    wcag_audit: WcagAudit = simplified_case.audit_overview.initial_wcag_audit
    home_page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit,
        page_type=WcagPageInitial.Type.HOME,
    )
    home_page.name = HOME_PAGE_NAME
    home_page.url = "https://example.com"
    home_page.save()
    pdf_page: WcagPageInitial = WcagPageInitial.objects.get(
        wcag_audit=wcag_audit,
        page_type=WcagPageInitial.Type.PDF,
    )
    pdf_page.name = PDF_PAGE_NAME
    pdf_page.url = "https://example.com/pdf"
    pdf_page.save()
    Report.objects.create(base_case=simplified_case)

    issues_tables: list[IssueTable] = build_issues_tables(
        pages=wcag_audit.testable_wcag_page_initials
    )

    assert len(issues_tables) == 6

    assert issues_tables[0].page.name == HOME_PAGE_NAME
    assert issues_tables[4].page.name == PDF_PAGE_NAME


@pytest.mark.django_db
def test_build_report_context():
    """Test context to render report built"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    WcagAudit.objects.create(simplified_case=simplified_case)
    StatementAudit.objects.create(simplified_case=simplified_case)
    AuditOverview.objects.create(simplified_case=simplified_case)
    report: Report = Report.objects.create(base_case=simplified_case)

    report_context: dict[
        str, Report | list[IssueTable] | AuditOverview | StatementAudit | WcagAudit
    ] = build_report_context(report=report)

    assert report_context == {
        "simplified_case": simplified_case,
        "audit_overview": simplified_case.audit_overview,
        "wcag_audit": simplified_case.audit_overview.initial_wcag_audit,
        "statement_audit": simplified_case.audit_overview.initial_statement_audit,
        "issues_tables": [],
        "report": report,
    }
