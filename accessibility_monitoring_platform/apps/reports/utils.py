# pylint: disable=all
"""
Utilities for reports app
"""
from typing import Optional

from django.db.models import QuerySet
from django.http import HttpRequest
from django.template import Context, Template

from ..common.utils import (
    get_id_from_button_name,
    record_model_update_event,
)

from .models import (
    Report,
    BaseTemplate,
    Section,
    TableRow,
    TEMPLATE_TYPE_URLS,
    TEMPLATE_TYPE_ISSUES,
)

WCAG_DEFINITION_BOILERPLATE_TEMPLATE = """{% if wcag_definition.url_on_w3 %}[{{ wcag_definition.name }}]({{ wcag_definition.url_on_w3 }}){% if wcag_definition.type == 'axe' %}: {{ wcag_definition.description|safe }}{% endif %}{% else %}{{ wcag_definition.name }}{% if wcag_definition.type == 'axe' %}: {{ wcag_definition.description|safe }}{% endif %}{% endif %}

{{ wcag_definition.report_boilerplate }}
"""
CHECK_RESULTS_NOTES_TEMPLATE = """{{ check_result.page }}

* {{ check_result.notes|safe }}"""
DELETE_ROW_BUTTON_PREFIX: str = "delete_table_row_"
UNDELETE_ROW_BUTTON_PREFIX: str = "undelete_table_row_"
MOVE_ROW_UP_BUTTON_PREFIX: str = "move_table_row_up_"
MOVE_ROW_DOWN_BUTTON_PREFIX: str = "move_table_row_down_"


def generate_report_content(report: Report) -> None:
    """
    Generate content of report sections.

    Args:
        report (Report): Report for which content is generated.
    """
    base_templates: QuerySet[BaseTemplate] = BaseTemplate.objects.all()
    report.section_set.all().delete()  # type: ignore
    context: Context = Context({"audit": report.case.audit})
    wcag_boilerplate_template: Template = Template(WCAG_DEFINITION_BOILERPLATE_TEMPLATE)
    check_result_notes_template: Template = Template(CHECK_RESULTS_NOTES_TEMPLATE)

    for base_template in base_templates:
        template: Template = Template(base_template.content)
        section: Section = Section.objects.create(
            report=report,
            name=base_template.name,
            template_type=base_template.template_type,
            content=template.render(context=context),
            position=base_template.position,
        )
        if report.case.audit:
            if section.template_type == TEMPLATE_TYPE_URLS:
                for row_number, page in enumerate(
                    report.case.audit.testable_pages, start=1
                ):
                    TableRow.objects.create(
                        section=section,
                        cell_content_1=str(page),
                        cell_content_2=f"[{page.url}]({page.url})",
                        row_number=row_number,
                    )
            elif section.template_type == TEMPLATE_TYPE_ISSUES:
                for row_number, check_result in enumerate(
                    report.case.audit.failed_check_results, start=1
                ):
                    wcag_boilerplate_context: Context = Context(
                        {"wcag_definition": check_result.wcag_definition}
                    )
                    check_result_context: Context = Context(
                        {"check_result": check_result}
                    )
                    TableRow.objects.create(
                        section=section,
                        cell_content_1=wcag_boilerplate_template.render(
                            context=wcag_boilerplate_context
                        ),
                        cell_content_2=check_result_notes_template.render(
                            context=check_result_context
                        ),
                        row_number=row_number,
                    )


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
        record_model_update_event(user=request.user, model_object=table_row_to_delete)  # type: ignore
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
        record_model_update_event(user=request.user, model_object=table_row_to_undelete)  # type: ignore
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
            section.tablerow_set.filter(row_number__lt=original_row_number)  # type: ignore
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
        table_row_to_swap_with: Optional[TableRow] = section.tablerow_set.filter(  # type: ignore
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


def get_report_viewer_url_prefix(request: HttpRequest) -> str:
    """Derive report viewer app's domain name from that of the platform in a request"""
    domain_name: str = request.META["HTTP_HOST"] if "HTTP_HOST" in request.META else ""
    if domain_name:
        if "localhost:8081" in domain_name:
            return "http://localhost:8082"
        elif "localhost:8001" in domain_name:
            return "http://localhost:8002"
        elif "accessibility-monitoring-platform-production" in domain_name:
            return "https://accessibility-monitoring-report-viewer-production.london.cloudapps.digital"
        elif "accessibility-monitoring-platform-test" in domain_name:
            return "https://accessibility-monitoring-report-viewer-test.london.cloudapps.digital"
        else:
            domain_name_split = domain_name.split(".")
            domain_name_split[0] = f"https://{domain_name_split[0]}-report-viewer"
            return ".".join(domain_name_split)
    else:
        return ""
