# pylint: disable=all
"""
Utilities for reports app
"""
from typing import Dict, List, Optional, Set

from django.db.models import QuerySet
from django.template import Context, Template
from django.utils.text import slugify

from ..cases.models import Case

from ..audits.models import Page, PAGE_TYPE_PDF, WcagDefinition

from .models import (
    Report,
    BaseTemplate,
    TEMPLATE_TYPE_URLS,
    TEMPLATE_TYPE_ISSUES_INTRO,
    TEMPLATE_TYPE_ISSUES_TABLE,
)

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
        name,
        template_type,
        content,
        position,
        editable_url_name,
        editable_url_label,
        editable_id=None,
        new_page=False,
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

    # @property
    # def visible_table_rows(self):
    #     return self.tablerow_set.filter(is_deleted=False)


class TableRow:
    """
    Class for row of table in report
    """

    def __init__(self, cell_content_1, cell_content_2, row_number):
        self.cell_content_1 = cell_content_1
        self.cell_content_2 = cell_content_2
        self.row_number = row_number


def build_report_sections(report: Report) -> List[Section]:
    """
    Generate content of report sections.

    Args:
        report (Report): Report for which content is generated.
    """
    top_level_base_templates: QuerySet[BaseTemplate] = BaseTemplate.objects.exclude(
        template_type=TEMPLATE_TYPE_ISSUES_TABLE
    )
    issues_table_base_template: BaseTemplate = BaseTemplate.objects.get(
        template_type=TEMPLATE_TYPE_ISSUES_TABLE
    )
    context: Context = Context({"audit": report.case.audit})
    issues_table_template: Template = Template(issues_table_base_template.content)
    section_position: int = 0
    used_wcag_definitions: Set[WcagDefinition] = set()
    sections: List[Section] = []

    for base_template in top_level_base_templates:
        template: Template = Template(base_template.content)
        section_position += 1
        if base_template.editable_url_name and report.case.audit:
            editable_id: int = report.case.audit.id
        else:
            editable_id: Optional[int] = None
        section: Section = Section(
            name=base_template.name,
            template_type=base_template.template_type,
            content=template.render(context=context),
            position=section_position,
            new_page=base_template.new_page,
            editable_url_name=base_template.editable_url_name,
            editable_url_label=base_template.editable_url_label,
            editable_id=editable_id,
        )
        if report.case.audit:
            if section.template_type == TEMPLATE_TYPE_URLS:
                section.table_rows = build_url_table_rows(report=report)
                sections.append(section)
            elif section.template_type == TEMPLATE_TYPE_ISSUES_INTRO:
                # Create an issues table section for each testable page
                sections.append(section)
                for page in report.case.audit.testable_pages:
                    page_context: Context = Context({"page": page})
                    section_position += 1
                    section_name: str = (
                        f"{page} page issues"
                        if page.page_type != PAGE_TYPE_PDF
                        else f"{page} issues"
                    )
                    page_section: Section = Section(
                        name=section_name,
                        template_type=TEMPLATE_TYPE_ISSUES_TABLE,
                        content=issues_table_template.render(context=page_context),
                        position=section_position,
                        new_page=issues_table_base_template.new_page,
                        editable_url_name="audits:edit-audit-page-checks",
                        editable_url_label=f"Edit test > {page}",
                        editable_id=page.id,
                    )
                    page_section.table_rows = build_issue_table_rows(
                        page=page,
                        used_wcag_definitions=used_wcag_definitions,
                    )
                    sections.append(page_section)
            else:
                sections.append(section)
        else:
            sections.append(section)
    return sections


def build_url_table_rows(report: Report) -> List[TableRow]:
    """Build url table row data for a testable page in the report"""
    table_rows: List[TableRow] = []
    for row_number, page in enumerate(report.case.audit.testable_pages, start=1):  # type: ignore
        table_rows.append(
            TableRow(
                cell_content_1=str(page),
                cell_content_2=f"[{page.url}]({page.url})",
                row_number=row_number,
            )
        )
    return table_rows


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
