"""
Test forms of reports app
"""
import pytest

from ...cases.models import Case

from ..forms import SectionUpdateForm, ReportFeedbackForm
from ..models import Report, Section


@pytest.mark.django_db
def test_section_update_form_html_without_script_tag():
    """Tests form is valid if html content field does not contain a script tag"""
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)
    section: Section = Section.objects.create(report=report, position=1)
    form: SectionUpdateForm = SectionUpdateForm(
        data={
            "version": 1,
            "template_type": "html",
            "content": "Not a script tag",
        },
        instance=section,
    )
    assert form.is_valid()


@pytest.mark.django_db
def test_section_update_form_html_with_script_tag():
    """Tests form is not valid if html content field contains a script tag"""
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)
    section: Section = Section.objects.create(report=report, position=1)
    form: SectionUpdateForm = SectionUpdateForm(
        data={
            "version": 1,
            "template_type": "html",
            "content": "Oh oh, a <script> tag",
        },
        instance=section,
    )
    assert not form.is_valid()
    assert form.errors == {"content": ["<script> tags are not allowed"]}


@pytest.mark.django_db
def test_section_update_form_markdown_with_script_tag():
    """Tests form is valid if markdown content field contains a script tag"""
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)
    section: Section = Section.objects.create(report=report, position=1)
    form: SectionUpdateForm = SectionUpdateForm(
        data={
            "version": 1,
            "template_type": "markdown",
            "content": "Oh oh, a <script> tag",
        },
        instance=section,
    )
    assert form.is_valid()


@pytest.mark.django_db
def test_report_feedback_is_valid():
    """Tests report feeback form is valid"""
    form: ReportFeedbackForm = ReportFeedbackForm(
        data={
            "what_were_you_trying_to_do": "text",
            "what_went_wrong": "text",
        }
    )
    assert form.is_valid()
