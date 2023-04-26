# pylint: disable=all
"""
Utilities for reports app
"""
from typing import Dict, Optional, Set

from django.db.models import QuerySet
from django.http import HttpRequest
from django.template import Context, Template
from django.utils import timezone

from ..cases.models import Case

from ..common.utils import (
    get_id_from_button_name,
    record_model_update_event,
)
from ..audits.models import Page, PAGE_TYPE_PDF, WcagDefinition

from .models import (
    Report,
    BaseTemplate,
    Section,
    TableRow,
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


def generate_report_content(report: Report) -> None:
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
    report.section_set.all().delete()
    context: Context = Context({"audit": report.case.audit})
    issues_table_template: Template = Template(issues_table_base_template.content)
    section_position: int = 0
    used_wcag_definitions: Set[WcagDefinition] = set()

    for base_template in top_level_base_templates:
        template: Template = Template(base_template.content)
        section_position += 1
        section: Section = Section.objects.create(
            report=report,
            name=base_template.name,
            template_type=base_template.template_type,
            content=template.render(context=context),
            position=section_position,
            new_page=base_template.new_page,
        )
        if report.case.audit:
            if section.template_type == TEMPLATE_TYPE_URLS:
                create_url_table_rows(report=report, section=section)
            elif section.template_type == TEMPLATE_TYPE_ISSUES_INTRO:
                # Create an issues table section for each testable page
                for page in report.case.audit.testable_pages:
                    page_context: Context = Context({"page": page})
                    section_position += 1
                    section_name: str = (
                        f"{page} page issues"
                        if page.page_type != PAGE_TYPE_PDF
                        else f"{page} issues"
                    )
                    page_section: Section = Section.objects.create(
                        report=report,
                        name=section_name,
                        template_type=TEMPLATE_TYPE_ISSUES_TABLE,
                        content=issues_table_template.render(context=page_context),
                        position=section_position,
                        new_page=issues_table_base_template.new_page,
                    )
                    used_wcag_definitions: Set[
                        WcagDefinition
                    ] = create_issue_table_rows(
                        page=page,
                        page_section=page_section,
                        used_wcag_definitions=used_wcag_definitions,
                    )
    report.report_rebuilt = timezone.now()
    report.save()


def create_url_table_rows(report: Report, section: Section) -> None:
    """Create url table row data for each testable page in the report"""
    for row_number, page in enumerate(report.case.audit.testable_pages, start=1):  # type: ignore
        TableRow.objects.create(
            section=section,
            cell_content_1=str(page),
            cell_content_2=f"[{page.url}]({page.url})",
            row_number=row_number,
        )


def create_issue_table_rows(
    page: Page, page_section: Section, used_wcag_definitions: Set[WcagDefinition]
) -> Set[WcagDefinition]:
    """Create issue table row data for each failed check for a page in the report"""
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
        TableRow.objects.create(
            section=page_section,
            cell_content_1=wcag_boilerplate_template.render(
                context=wcag_boilerplate_context
            ),
            cell_content_2=check_result_notes_template.render(
                context=check_result_context
            ),
            row_number=row_number,
        )
    return used_wcag_definitions


def delete_table_row(request: HttpRequest) -> Optional[int]:
    """
    Look for a button name in the request POST which indicates a
    table row is to be deleted. If found, delete the row.

    Args:
        request (HttpRequest): The HTTP request.
    """
    table_row_id_to_delete: Optional[int] = get_id_from_button_name(
        button_name_prefix=DELETE_ROW_BUTTON_PREFIX,
        querydict=request.POST,
    )
    if table_row_id_to_delete is not None:
        table_row_to_delete: TableRow = TableRow.objects.get(id=table_row_id_to_delete)
        table_row_to_delete.is_deleted = True
        record_model_update_event(user=request.user, model_object=table_row_to_delete)
        table_row_to_delete.save()
        return table_row_id_to_delete


def undelete_table_row(request: HttpRequest) -> Optional[int]:
    """
    Look for a button name in the request POST which indicates a
    table row is to be undeleted. If found, undelete the row.

    Args:
        request (HttpRequest): The HTTP request.
    """
    table_row_id_to_undelete: Optional[int] = get_id_from_button_name(
        button_name_prefix=UNDELETE_ROW_BUTTON_PREFIX,
        querydict=request.POST,
    )
    if table_row_id_to_undelete is not None:
        table_row_to_undelete: TableRow = TableRow.objects.get(
            id=table_row_id_to_undelete
        )
        table_row_to_undelete.is_deleted = False
        record_model_update_event(user=request.user, model_object=table_row_to_undelete)
        table_row_to_undelete.save()
        return table_row_id_to_undelete


def move_table_row_up(request: HttpRequest, section: Section) -> Optional[int]:
    """
    Look for a button name in the request POST which indicates a
    table row is to be moved up. If found, move the row up.

    Args:
        request (HttpRequest): The HTTP request.
    """
    table_row_id_to_move_up: Optional[int] = get_id_from_button_name(
        button_name_prefix=MOVE_ROW_UP_BUTTON_PREFIX,
        querydict=request.POST,
    )
    if table_row_id_to_move_up is not None:
        table_row_to_move_up: TableRow = TableRow.objects.get(
            id=table_row_id_to_move_up
        )
        original_row_number: int = table_row_to_move_up.row_number
        table_row_to_swap_with: Optional[TableRow] = (
            section.tablerow_set.filter(row_number__lt=original_row_number)
            .order_by("-row_number")
            .first()
        )
        if table_row_to_swap_with:
            table_row_to_move_up.row_number = table_row_to_swap_with.row_number
            table_row_to_move_up.save()
            table_row_to_swap_with.row_number = original_row_number
            table_row_to_swap_with.save()
        return table_row_id_to_move_up


def move_table_row_down(request: HttpRequest, section: Section) -> Optional[int]:
    """
    Look for a button name in the request POST which indicates a
    table row is to be moved down. If found, move the row down.

    Args:
        request (HttpRequest): The HTTP request.
    """
    table_row_id_to_move_down: Optional[int] = get_id_from_button_name(
        button_name_prefix=MOVE_ROW_DOWN_BUTTON_PREFIX,
        querydict=request.POST,
    )
    if table_row_id_to_move_down is not None:
        table_row_to_move_down: TableRow = TableRow.objects.get(
            id=table_row_id_to_move_down
        )
        original_row_number: int = table_row_to_move_down.row_number
        table_row_to_swap_with: Optional[TableRow] = section.tablerow_set.filter(
            row_number__gt=original_row_number
        ).first()
        if table_row_to_swap_with:
            table_row_to_move_down.row_number = table_row_to_swap_with.row_number
            table_row_to_move_down.save()
            table_row_to_swap_with.row_number = original_row_number
            table_row_to_swap_with.save()
        return table_row_id_to_move_down


def check_for_buttons_by_name(request: HttpRequest, section: Section) -> Optional[int]:
    """
    Check for buttons by name in request.
    If any are found then update the data accordingly.

    Args:
        request (HttpRequest): The HTTP request.
    """
    updated_table_row_id: Optional[int] = delete_table_row(request=request)
    if updated_table_row_id is None:
        updated_table_row_id = undelete_table_row(request=request)
    if updated_table_row_id is None:
        updated_table_row_id = move_table_row_up(request=request, section=section)
    if updated_table_row_id is None:
        updated_table_row_id = move_table_row_down(request=request, section=section)
    return updated_table_row_id


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
