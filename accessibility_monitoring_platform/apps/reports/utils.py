# pylint: disable=all
"""
Utilities for reports app
"""

from django.contrib import messages
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.template import Context, Template, loader
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from ..audits.models import Audit, CheckResult, Page, WcagDefinition
from ..cases.models import Case
from ..s3_read_write.models import S3Report
from ..s3_read_write.utils import S3ReadWriteReport
from .models import Report

WCAG_DEFINITION_BOILERPLATE_TEMPLATE: str = """{% if wcag_definition.url_on_w3 %}[{{ wcag_definition.name }}]({{ wcag_definition.url_on_w3 }}){% if wcag_definition.description and wcag_definition.type != 'manual' %}: {% endif %}{% else %}{{ wcag_definition.name }}{% if wcag_definition.description and wcag_definition.type != 'manual' %}: {% endif %}{% endif %}{% if wcag_definition.description and wcag_definition.type != 'manual' %}{{ wcag_definition.description|safe }}.{% endif %}
{% if first_use_of_wcag_definition %}
{{ wcag_definition.report_boilerplate|safe }}
{% endif %}"""
CHECK_RESULTS_NOTES_TEMPLATE: str = """{{ check_result.notes|safe }}"""
CHECK_RESULTS_RETEST_NOTES_TEMPLATE: str = """{{ check_result.retest_notes|safe }}"""
DELETE_ROW_BUTTON_PREFIX: str = "delete_table_row_"
UNDELETE_ROW_BUTTON_PREFIX: str = "undelete_table_row_"
MOVE_ROW_UP_BUTTON_PREFIX: str = "move_table_row_up_"
MOVE_ROW_DOWN_BUTTON_PREFIX: str = "move_table_row_down_"

wcag_boilerplate_template: Template = Template(WCAG_DEFINITION_BOILERPLATE_TEMPLATE)
check_result_notes_template: Template = Template(CHECK_RESULTS_NOTES_TEMPLATE)
check_result_retest_notes_template: Template = Template(
    CHECK_RESULTS_RETEST_NOTES_TEMPLATE
)


class Section:
    """
    Class for section of report
    """

    def __init__(
        self,
        name: str,
        template_type: str,
        content: str,
        position: int,
        editable_url_name: str,
        editable_url_label: str,
        editable_id: int | None = None,
        new_page: bool = False,
    ):
        self.name = name
        self.template_type = template_type
        self.content = content
        self.position = position
        self.new_page = new_page
        self.editable_url_name = editable_url_name
        self.editable_url_label = editable_url_label
        self.editable_id = editable_id
        self.table_rows = []

    @property
    def anchor(self) -> str:
        return f"report-section-{slugify(self.name)}"

    @property
    def has_table(self):
        return len(self.table_rows) > 0


class TableRow:
    """
    Class for row of table in report
    """

    def __init__(self, cell_content_1: str, cell_content_2: str, row_number: int):
        self.cell_content_1 = cell_content_1
        self.cell_content_2 = cell_content_2
        self.row_number = row_number


class IssueTable:
    """
    Class for issue table in
    """

    def __init__(self, page: Page, rows: list[TableRow]):
        self.page = page
        self.rows = rows

    @property
    def anchor(self) -> str:
        return f"issues-{slugify(self.page)}"


def build_issues_tables(
    pages: list[Page],
    check_results_attr: str = "failed_check_results",
    use_retest_notes: bool = False,
) -> list[IssueTable]:
    """
    Generate content of issues tables for report.
    """
    issues_tables: list[IssueTable] = []
    used_wcag_definitions: set[WcagDefinition] = set()
    for page in pages:
        issues_tables.append(
            IssueTable(
                page=page,
                rows=build_issue_table_rows(
                    check_results=getattr(page, check_results_attr),
                    used_wcag_definitions=used_wcag_definitions,
                    use_retest_notes=use_retest_notes,
                ),
            )
        )
    return issues_tables


def build_issue_table_rows(
    check_results: list[CheckResult],
    used_wcag_definitions: set[WcagDefinition],
    use_retest_notes: bool = False,
) -> list[TableRow]:
    """Build issue table row data for each failed check for a page in the report"""
    table_rows: list[TableRow] = []
    for row_number, check_result in enumerate(check_results, start=1):
        first_use_of_wcag_definition: bool = (
            check_result.wcag_definition not in used_wcag_definitions
        )
        if first_use_of_wcag_definition:
            used_wcag_definitions.add(check_result.wcag_definition)
        wcag_boilerplate_context: Context = Context(
            {
                "wcag_definition": check_result.wcag_definition,
                "first_use_of_wcag_definition": first_use_of_wcag_definition,
            }
        )
        check_result_context: Context = Context({"check_result": check_result})
        if use_retest_notes:
            notes_cell: str = check_result_retest_notes_template.render(
                context=check_result_context
            )
        else:
            notes_cell: str = check_result_notes_template.render(
                context=check_result_context
            )
        table_rows.append(
            TableRow(
                cell_content_1=wcag_boilerplate_template.render(
                    context=wcag_boilerplate_context
                ),
                cell_content_2=notes_cell,
                row_number=row_number,
            )
        )
    return table_rows


def build_report_context(
    report: Report,
) -> dict[str, Report | list[IssueTable] | Audit]:
    """Return context used to render report"""
    issues_tables: list[IssueTable] = (
        build_issues_tables(pages=report.case.audit.testable_pages)
        if report.case.audit is not None
        else []
    )
    return {
        "report": report,
        "issues_tables": issues_tables,
        "audit": report.case.audit,
    }


def get_report_visits_metrics(case: Case) -> dict[str, str]:
    """Returns the visit metrics for reports"""
    return {
        "number_of_visits": case.reportvisitsmetrics_set.all().count(),
        "number_of_unique_visitors": case.reportvisitsmetrics_set.values_list(
            "fingerprint_hash"
        )
        .distinct()
        .count(),
    }


def publish_report_util(report: Report, request: HttpRequest) -> None:
    """Publish report to S3"""
    template: Template = loader.get_template(
        f"""reports_common/accessibility_report_{report.report_version}.html"""
    )
    html: str = template.render(build_report_context(report=report), request)
    published_s3_reports: QuerySet[S3Report] = S3Report.objects.filter(case=report.case)
    for s3_report in published_s3_reports:
        s3_report.latest_published = False
        s3_report.save()
    s3_read_write_report: S3ReadWriteReport = S3ReadWriteReport()
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content=html,
        case=report.case,
        user=request.user,
        report_version=report.report_version,
    )
    messages.add_message(
        request,
        messages.INFO,
        mark_safe("HTML report successfully created!" ""),
    )
