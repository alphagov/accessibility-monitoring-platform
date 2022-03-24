# pylint: disable=all
"""
Utilities for reports app
"""

from django.db.models import QuerySet
from django.template import Context, Template

from .models import (
    Report,
    BaseTemplate,
    Section,
    TableRow,
    TEMPLATE_TYPE_URLS,
    TEMPLATE_TYPE_ISSUES,
)

WCAG_DEFINITION_BOILERPLATE_TEMPLATE = """{% if wcag_definition.url_on_w3 %}[{{ wcag_definition.name }}]({{ wcag_definition.url_on_w3 }}){% if wcag_definition.type == 'axe' %}: {{ wcag_definition.description }}{% endif %}{% else %}{{ wcag_definition.name }}{% if wcag_definition.type == 'axe' %}: {{ wcag_definition.description }}{% endif %}{% endif %}
{{ wcag_definition.report_boilerplate }}
"""


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

    for base_template in base_templates:
        template: Template = Template(base_template.content)
        section: Section = Section.objects.create(
            report=report,
            name=base_template.name,
            template_type=base_template.template_type,
            content=template.render(context=context),
            position=base_template.position,
        )
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
                TableRow.objects.create(
                    section=section,
                    cell_content_1=wcag_boilerplate_template.render(
                        context=wcag_boilerplate_context
                    ),
                    cell_content_2=check_result.notes,
                    row_number=row_number,
                )
