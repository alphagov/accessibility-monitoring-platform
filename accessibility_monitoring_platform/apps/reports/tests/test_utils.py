"""
Test utility functions of reports app
"""
import pytest
from typing import List, Set
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.http import HttpRequest
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
    Section,
    TableRow,
    BaseTemplate,
    ReportVisitsMetrics,
)
from ..utils import (
    check_for_buttons_by_name,
    delete_table_row,
    move_table_row_down,
    move_table_row_up,
    generate_report_content,
    create_url_table_rows,
    create_issue_table_rows,
    undelete_table_row,
    get_report_viewer_url_prefix,
    get_report_visits_metrics,
    DELETE_ROW_BUTTON_PREFIX,
    UNDELETE_ROW_BUTTON_PREFIX,
    MOVE_ROW_UP_BUTTON_PREFIX,
    MOVE_ROW_DOWN_BUTTON_PREFIX,
)

NUMBER_OF_TOP_LEVEL_BASE_TEMPLATES: int = 9
PREVIOUS_ROW_POSITION: int = 1
ORIGINAL_ROW_POSITION: int = 2
NEXT_ROW_POSITION: int = 3
HOME_PAGE_NAME: str = "Home name"
PDF_PAGE_NAME: str = "PDF name"
HOME_PAGE_URL: str = "https://example.com/home"
PDF_PAGE_URL: str = "https://example.com/pdf"
CHECK_RESULT_NOTES: str = "Check results note"


class MockRequest:
    def __init__(self, http_host: str):
        self.META = {"HTTP_HOST": http_host}  # pylint: disable=invalid-name


def create_table_row() -> TableRow:
    """Create a table row"""
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)
    section: Section = Section.objects.create(report=report, position=1)
    return TableRow.objects.create(section=section, row_number=1)


@pytest.mark.django_db
def test_generate_report_content():
    """Test new reports use BaseTemplates to create their sections"""
    top_level_base_templates: List[BaseTemplate] = list(
        BaseTemplate.objects.exclude(template_type=TEMPLATE_TYPE_ISSUES_TABLE)
    )
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    context: Context = Context({"audit": audit})
    report: Report = Report.objects.create(case=case)

    generate_report_content(report=report)

    top_level_sections: List[Section] = list(report.top_level_sections)  # type: ignore

    assert len(top_level_base_templates) == NUMBER_OF_TOP_LEVEL_BASE_TEMPLATES
    assert len(top_level_sections) == NUMBER_OF_TOP_LEVEL_BASE_TEMPLATES

    for section, base_template in zip(top_level_sections, top_level_base_templates):
        assert section.name == base_template.name
        assert section.template_type == base_template.template_type
        assert section.position == base_template.position

        template: Template = Template(base_template.content)
        assert section.content == template.render(context=context)


@pytest.mark.django_db
def test_create_url_table_rows():
    """Test url table row created for page"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit,
        name=HOME_PAGE_NAME,
        page_type=PAGE_TYPE_HOME,
        url=HOME_PAGE_URL,
    )
    report: Report = Report.objects.create(case=case)
    section: Section = Section.objects.create(report=report, position=1)

    create_url_table_rows(report=report, section=section)

    table_rows: QuerySet[TableRow] = TableRow.objects.all()

    assert table_rows.count() == 1

    assert HOME_PAGE_NAME in table_rows[0].cell_content_1
    assert HOME_PAGE_URL in table_rows[0].cell_content_2


@pytest.mark.django_db
def test_create_issue_table_rows():
    """Test issue table row created for failed check"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(
        audit=audit,
        name=HOME_PAGE_NAME,
        page_type=PAGE_TYPE_HOME,
        url=HOME_PAGE_URL,
    )
    report: Report = Report.objects.create(case=case)
    section: Section = Section.objects.create(report=report, position=1)
    wcag_definition: WcagDefinition = WcagDefinition.objects.filter(  # type: ignore
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

    create_issue_table_rows(
        page=page, page_section=section, used_wcag_definitions=used_wcag_definitions
    )

    table_rows: QuerySet[TableRow] = TableRow.objects.all()

    assert table_rows.count() == 1

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
    wcag_definition: WcagDefinition = WcagDefinition.objects.filter(  # type: ignore
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

    generate_report_content(report=report)

    table_rows: QuerySet[TableRow] = TableRow.objects.filter(
        cell_content_1__contains=wcag_definition.name
    )

    assert table_rows.count() == 2

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

    generate_report_content(report=report)

    issues_table_sections: QuerySet[Section] = report.section_set.filter(  # type: ignore
        template_type=TEMPLATE_TYPE_ISSUES_TABLE
    )

    assert issues_table_sections.count() == 2

    assert issues_table_sections[0].name == f"{HOME_PAGE_NAME} page issues"
    assert issues_table_sections[1].name == f"{PDF_PAGE_NAME} issues"


@pytest.mark.parametrize(
    "first_return, second_return, third_return, fourth_return, overall_return",
    [
        (None, None, None, None, None),
        (1, None, None, None, 1),
        (None, 2, None, None, 2),
        (None, None, 3, None, 3),
        (None, None, None, 4, 4),
    ],
)
def test_check_for_buttons_by_name(
    first_return, second_return, third_return, fourth_return, overall_return
):
    """
    Test check_for_buttons_by_name calls functions until an id is returned and then
    returns that id.
    """
    mock_request: HttpRequest = HttpRequest()
    mock_section: Section = Section()
    with patch(
        "accessibility_monitoring_platform.apps.reports.utils.delete_table_row",
        return_value=first_return,
    ) as mock_delete_table_row, patch(
        "accessibility_monitoring_platform.apps.reports.utils.undelete_table_row",
        return_value=second_return,
    ) as mock_undelete_table_row, patch(
        "accessibility_monitoring_platform.apps.reports.utils.move_table_row_up",
        return_value=third_return,
    ) as mock_move_table_row_up, patch(
        "accessibility_monitoring_platform.apps.reports.utils.move_table_row_down",
        return_value=fourth_return,
    ) as mock_move_table_row_down:
        assert check_for_buttons_by_name(mock_request, mock_section) == overall_return

    mock_delete_table_row.assert_called_once()

    if first_return is None:
        mock_undelete_table_row.assert_called_once()
        if second_return is None:
            mock_move_table_row_up.assert_called_once()
            if third_return is None:
                mock_move_table_row_down.assert_called_once()
            else:
                mock_move_table_row_down.assert_not_called()
        else:
            mock_move_table_row_up.assert_not_called()
            mock_move_table_row_down.assert_not_called()
    else:
        mock_undelete_table_row.assert_not_called()
        mock_move_table_row_up.assert_not_called()
        mock_move_table_row_down.assert_not_called()


@pytest.mark.django_db
def test_delete_table_row(rf):
    """Test delete_table_row marks table row as deleted"""
    table_row: TableRow = create_table_row()
    table_row_id: int = table_row.id  # type: ignore
    request: HttpRequest = rf.post(
        "/", {f"{DELETE_ROW_BUTTON_PREFIX}{table_row_id}": "Button"}
    )
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@…", password="secret"
    )
    request.user = user

    assert not table_row.is_deleted

    delete_table_row(request=request)

    updated_table_row: TableRow = TableRow.objects.get(id=table_row_id)
    assert updated_table_row.is_deleted


@pytest.mark.django_db
def test_undelete_table_row(rf):
    """Test undelete_table_row marks table row as not deleted"""
    table_row: TableRow = create_table_row()
    table_row_id: int = table_row.id  # type: ignore
    request: HttpRequest = rf.post(
        "/", {f"{UNDELETE_ROW_BUTTON_PREFIX}{table_row_id}": "Button"}
    )
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@…", password="secret"
    )
    request.user = user

    table_row.is_deleted = True
    table_row.save()

    undelete_table_row(request=request)

    updated_table_row: TableRow = TableRow.objects.get(id=table_row_id)
    assert not updated_table_row.is_deleted


@pytest.mark.django_db
def test_move_table_row_up(rf):
    """Test move_table_row_up swaps table row's position with the previous"""
    table_row: TableRow = create_table_row()
    table_row_id: int = table_row.id  # type: ignore
    table_row.row_number = ORIGINAL_ROW_POSITION
    table_row.save()
    previous_row: TableRow = TableRow.objects.create(
        section=table_row.section, row_number=PREVIOUS_ROW_POSITION
    )

    request: HttpRequest = rf.post(
        "/", {f"{MOVE_ROW_UP_BUTTON_PREFIX}{table_row_id}": "Button"}
    )

    move_table_row_up(request=request, section=table_row.section)

    updated_table_row: TableRow = TableRow.objects.get(id=table_row_id)
    updated_previous_row: TableRow = TableRow.objects.get(id=previous_row.id)  # type: ignore

    assert updated_table_row.row_number == PREVIOUS_ROW_POSITION
    assert updated_previous_row.row_number == ORIGINAL_ROW_POSITION


@pytest.mark.django_db
def test_move_table_row_down(rf):
    """Test move_table_row_down swaps table row's position with the next"""
    table_row: TableRow = create_table_row()
    table_row_id: int = table_row.id  # type: ignore
    table_row.row_number = ORIGINAL_ROW_POSITION
    table_row.save()
    next_row: TableRow = TableRow.objects.create(
        section=table_row.section, row_number=NEXT_ROW_POSITION
    )

    request: HttpRequest = rf.post(
        "/", {f"{MOVE_ROW_DOWN_BUTTON_PREFIX}{table_row_id}": "Button"}
    )

    move_table_row_down(request=request, section=table_row.section)

    updated_table_row: TableRow = TableRow.objects.get(id=table_row_id)
    updated_next_row: TableRow = TableRow.objects.get(id=next_row.id)  # type: ignore

    assert updated_table_row.row_number == NEXT_ROW_POSITION
    assert updated_next_row.row_number == ORIGINAL_ROW_POSITION


@pytest.mark.parametrize(
    "http_host, res",
    [
        ("http://localhost:8081", "http://localhost:8082"),
        ("http://localhost:8001", "http://localhost:8002"),
        (
            "https://accessibility-monitoring-platform-production.com",
            "https://reports.accessibility-monitoring.service.gov.uk",
        ),
        (
            "https://platform.accessibility-monitoring.gov.uk",
            "https://reports.accessibility-monitoring.service.gov.uk",
        ),
        (
            "https://accessibility-monitoring-platform-test.com",
            "https://reports-test.accessibility-monitoring.service.gov.uk",
        ),
        (
            "https://platform-test.accessibility-monitoring.gov.uk",
            "https://reports-test.accessibility-monitoring.service.gov.uk",
        ),
        ("https://512-local-branch.com", "http://512-local-branch-report-viewer.com"),
        ("", ""),
    ],
)
def test_report_viewer_url(http_host, res):
    mock_request: MockRequest = MockRequest(http_host=http_host)
    return res == get_report_viewer_url_prefix(request=mock_request)  # type: ignore


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
