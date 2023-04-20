# pylint: disable=all
"""
Utilities for reports app
"""
from typing import Dict, List, Optional, Set

from django.template import Context, Template
from django.utils.text import slugify

from ..cases.models import Case

from ..audits.models import Page, WcagDefinition

from .models import Report

WCAG_DEFINITION_BOILERPLATE_TEMPLATE: str = """{% if wcag_definition.url_on_w3 %}[{{ wcag_definition.name }}]({{ wcag_definition.url_on_w3 }}){% if wcag_definition.description and wcag_definition.type != 'manual' %}: {% endif %}{% else %}{{ wcag_definition.name }}{% if wcag_definition.description and wcag_definition.type != 'manual' %}: {% endif %}{% endif %}{% if wcag_definition.description and wcag_definition.type != 'manual' %}{{ wcag_definition.description|safe }}.{% endif %}
{% if first_use_of_wcag_definition %}
{{ wcag_definition.report_boilerplate|safe }}
{% endif %}"""
CHECK_RESULTS_NOTES_TEMPLATE: str = """{{ check_result.notes|safe }}"""
DELETE_ROW_BUTTON_PREFIX: str = "delete_table_row_"
UNDELETE_ROW_BUTTON_PREFIX: str = "undelete_table_row_"
MOVE_ROW_UP_BUTTON_PREFIX: str = "move_table_row_up_"
MOVE_ROW_DOWN_BUTTON_PREFIX: str = "move_table_row_down_"

wcag_boilerplate_template: Template = Template(WCAG_DEFINITION_BOILERPLATE_TEMPLATE)
check_result_notes_template: Template = Template(CHECK_RESULTS_NOTES_TEMPLATE)


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
        editable_id: Optional[int] = None,
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

    def __init__(self, page: Page, rows: List[TableRow]):
        self.page = page
        self.rows = rows

    @property
    def anchor(self) -> str:
        return f"issues-{slugify(self.page)}"


def build_issues_tables(report: Report) -> List[IssueTable]:
    """
    Generate content of issues tables for report.

    Args:
        report (Report): Report for which content is generated.
    """
    issues_tables: List[IssueTable] = []
    if report.case.audit:
        used_wcag_definitions: Set[WcagDefinition] = set()
        for page in report.case.audit.testable_pages:
            issues_tables.append(
                IssueTable(
                    page=page,
                    rows=build_issue_table_rows(
                        page=page,
                        used_wcag_definitions=used_wcag_definitions,
                    ),
                )
            )
    return issues_tables


def build_issue_table_rows(
    page: Page, used_wcag_definitions: Set[WcagDefinition]
) -> List[TableRow]:
    """Build issue table row data for each failed check for a page in the report"""
    table_rows: List[TableRow] = []
    for row_number, check_result in enumerate(page.failed_check_results, start=1):
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
        table_rows.append(
            TableRow(
                cell_content_1=wcag_boilerplate_template.render(
                    context=wcag_boilerplate_context
                ),
                cell_content_2=check_result_notes_template.render(
                    context=check_result_context
                ),
                row_number=row_number,
            )
        )
    return table_rows


def get_report_visits_metrics(case: Case) -> Dict[str, str]:
    """Returns the visit metrics for reports"""
    return {
        "number_of_visits": case.reportvisitsmetrics_set.all().count(),
        "number_of_unique_visitors": case.reportvisitsmetrics_set.values_list(
            "fingerprint_hash"
        )
        .distinct()
        .count(),
    }
