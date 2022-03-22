"""
Test utility functions of reports app
"""
import pytest
from typing import List

from django.template import Context, Template

from ...audits.models import Audit
from ...cases.models import Case

from ..models import Report, Section, BaseTemplate
from ..utils import generate_report_content

NUMBER_OF_BASE_TEMPLATES: int = 9


@pytest.mark.django_db
def test_generate_report_content():
    """Test new reports use BaseTemplates to create their sections"""
    base_templates: List[BaseTemplate] = list(BaseTemplate.objects.all())
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    context: Context = Context({"audit": audit})
    report: Report = Report.objects.create(case=case)

    generate_report_content(report=report)

    sections: List[Section] = list(report.section_set.all())  # type: ignore

    assert len(base_templates) == NUMBER_OF_BASE_TEMPLATES
    assert len(sections) == NUMBER_OF_BASE_TEMPLATES

    for section, base_template in zip(sections, base_templates):
        assert section.name == base_template.name
        assert section.template_type == base_template.template_type
        assert section.position == base_template.position

        template: Template = Template(base_template.content)
        assert section.content == template.render(context=context)
