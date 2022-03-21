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
)


def generate_report_content(report: Report) -> None:
    """
    Generate content of report sections.

    Args:
        report (Report): Report for which content is generated.
    """
    base_templates: QuerySet[BaseTemplate] = BaseTemplate.objects.all()
    report.section_set.all().delete()  # type: ignore
    context: Context = Context({"audit": report.case.audit})

    for base_template in base_templates:
        template: Template = Template(base_template.content)
        Section.objects.create(
            report=report,
            name=base_template.name,
            template_type=base_template.template_type,
            content=template.render(context=context),
            position=base_template.position,
        )
