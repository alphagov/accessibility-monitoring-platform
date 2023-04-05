"""
Test utility functions of reports app
"""
import pytest
from typing import List, Set

from django.template import Context, Template

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
    BaseTemplate,
    ReportVisitsMetrics,
)
from ..utils import (
    Section,
    TableRow,
    build_report_sections,
    build_issue_table_rows,
    build_url_table_rows,
    get_report_visits_metrics,
)

NUMBER_OF_TOP_LEVEL_BASE_TEMPLATES: int = 9
HOME_PAGE_NAME: str = "Home name"
PDF_PAGE_NAME: str = "PDF name"
HOME_PAGE_URL: str = "https://example.com/home"
PDF_PAGE_URL: str = "https://example.com/pdf"
CHECK_RESULT_NOTES: str = "Check results note <span>including HTML</span>"


@pytest.mark.django_db
def test_build_report_sections():
    """Test build_report_sections uses BaseTemplates to build sections"""
    top_level_base_templates: List[BaseTemplate] = list(
        BaseTemplate.objects.exclude(template_type=TEMPLATE_TYPE_ISSUES_TABLE)
    )
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    context: Context = Context({"audit": audit})
    report: Report = Report.objects.create(case=case)

    sections: List[Section] = build_report_sections(report=report)

    assert len(top_level_base_templates) == NUMBER_OF_TOP_LEVEL_BASE_TEMPLATES
    assert len(sections) == NUMBER_OF_TOP_LEVEL_BASE_TEMPLATES

    for section, base_template in zip(sections, top_level_base_templates):
        assert section.name == base_template.name
        assert section.template_type == base_template.template_type
        assert section.position == base_template.position

        template: Template = Template(base_template.content)
        assert section.content == template.render(context=context)


@pytest.mark.django_db
def test_build_url_table_rows():
    """Test url table rows built for page"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit,
        name=HOME_PAGE_NAME,
        page_type=PAGE_TYPE_HOME,
        url=HOME_PAGE_URL,
    )
    report: Report = Report.objects.create(case=case)

    table_rows: List[TableRow] = build_url_table_rows(report=report)

    assert len(table_rows) == 1

    assert HOME_PAGE_NAME in table_rows[0].cell_content_1
    assert HOME_PAGE_URL in table_rows[0].cell_content_2


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

    sections: List[Section] = build_report_sections(report=report)

    table_rows: List[TableRow] = []
    for section in sections:
        for table_row in section.table_rows:
            if wcag_definition.name in table_row.cell_content_1:
                table_rows.append(table_row)

    assert len(table_rows) == 2

    assert wcag_definition.name in table_rows[0].cell_content_1
    assert wcag_definition.report_boilerplate in table_rows[0].cell_content_1
    assert wcag_definition.name in table_rows[1].cell_content_1
    assert wcag_definition.report_boilerplate not in table_rows[1].cell_content_1


@pytest.mark.django_db
def test_generate_report_content_issues_table_sections():
    """Test report contains issues table sections for each page"""
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

    sections: List[Section] = build_report_sections(report=report)

    issues_table_sections: List[Section] = [
        section
        for section in sections
        if section.template_type == TEMPLATE_TYPE_ISSUES_TABLE
    ]

    assert len(issues_table_sections) == 2

    assert issues_table_sections[0].name == f"{HOME_PAGE_NAME} page issues"
    assert issues_table_sections[1].name == f"{PDF_PAGE_NAME} issues"


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
