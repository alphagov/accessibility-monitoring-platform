"""
Test utility functions of reports app
"""
import pytest
from typing import List, Set

from ...audits.models import (
    Audit,
    CheckResult,
    Page,
    WcagDefinition,
    CHECK_RESULT_ERROR,
    PAGE_TYPE_HOME,
    PAGE_TYPE_PDF,
    TEST_TYPE_PDF,
)
from ...cases.models import Case

from ..models import (
    TEMPLATE_TYPE_ISSUES_TABLE,
    Report,
    ReportVisitsMetrics,
)
from ..utils import (
    IssueTable,
    TableRow,
    build_issues_tables,
    build_issue_table_rows,
    get_report_visits_metrics,
)

NUMBER_OF_TOP_LEVEL_BASE_TEMPLATES: int = 9
HOME_PAGE_NAME: str = "Home name"
PDF_PAGE_NAME: str = "PDF name"
HOME_PAGE_URL: str = "https://example.com/home"
PDF_PAGE_URL: str = "https://example.com/pdf"
CHECK_RESULT_NOTES: str = "Check results note <span>including HTML</span>"


@pytest.mark.django_db
def test_build_issue_table_rows():
    """Test issue table row created for failed check"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(
        audit=audit,
        name=HOME_PAGE_NAME,
        page_type=PAGE_TYPE_HOME,
        url=HOME_PAGE_URL,
    )
    wcag_definition: WcagDefinition = WcagDefinition.objects.filter(
        type=TEST_TYPE_PDF
    ).first()
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CHECK_RESULT_ERROR,
        notes=CHECK_RESULT_NOTES,
    )
    used_wcag_definitions: Set[WcagDefinition] = set()

    table_rows: List[TableRow] = build_issue_table_rows(
        page=page, used_wcag_definitions=used_wcag_definitions
    )

    assert len(table_rows) == 1

    assert wcag_definition.name in table_rows[0].cell_content_1
    assert CHECK_RESULT_NOTES in table_rows[0].cell_content_2


@pytest.mark.django_db
def test_report_boilerplate_shown_only_once():
    """
    Test report contains WCAG definition's boilerplate text
    only the first time that definition appears.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    first_page: Page = Page.objects.create(
        audit=audit,
        name=HOME_PAGE_NAME,
        page_type=PAGE_TYPE_HOME,
        url=HOME_PAGE_URL,
    )
    second_page: Page = Page.objects.create(
        audit=audit,
        name=PDF_PAGE_NAME,
        page_type=PAGE_TYPE_PDF,
        url=PDF_PAGE_URL,
    )
    report: Report = Report.objects.create(case=case)
    wcag_definition: WcagDefinition = WcagDefinition.objects.filter(
        type=TEST_TYPE_PDF
    ).first()
    CheckResult.objects.create(
        audit=audit,
        page=first_page,
        wcag_definition=wcag_definition,
        check_result_state=CHECK_RESULT_ERROR,
    )
    CheckResult.objects.create(
        audit=audit,
        page=second_page,
        wcag_definition=wcag_definition,
        check_result_state=CHECK_RESULT_ERROR,
    )

    issues_tables: List[IssueTable] = build_issues_tables(report=report)

    table_rows: List[TableRow] = []
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
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit,
        name=HOME_PAGE_NAME,
        page_type=PAGE_TYPE_HOME,
        url="https://example.com",
    )
    Page.objects.create(
        audit=audit,
        name=PDF_PAGE_NAME,
        page_type=PAGE_TYPE_PDF,
        url="https://example.com/pdf",
    )
    report: Report = Report.objects.create(case=case)

    issues_tables: List[IssueTable] = build_issues_tables(report=report)

    assert len(issues_tables) == 2

    assert issues_tables[0].page.name == HOME_PAGE_NAME
    assert issues_tables[1].page.name == PDF_PAGE_NAME


@pytest.mark.django_db
def test_report_visits_metrics():
    case: Case = Case.objects.create()
    res = get_report_visits_metrics(case)
    assert res["number_of_visits"] == 0
    assert res["number_of_unique_visitors"] == 0
    ReportVisitsMetrics.objects.create(case=case, fingerprint_hash=1234)
    ReportVisitsMetrics.objects.create(case=case, fingerprint_hash=1234)
    res_2 = get_report_visits_metrics(case)
    assert res_2["number_of_visits"] == 2
    assert res_2["number_of_unique_visitors"] == 1
