"""
Test forms of audits app
"""
import pytest

from datetime import date

from ...cases.models import Case
from ..forms import AuditPageForm, AuditPageChecksForm
from ..models import Audit, Page


def test_url_is_required_in_audit_page_form():
    """Tests AuditPageForm's url field is required"""
    form: AuditPageForm = AuditPageForm(data={})

    assert not form.is_valid()
    assert form.errors == {"url": ["URL is required"]}


@pytest.mark.django_db
def test_next_page_choice_ticked_if_complete():
    """Check that next page choices are ticked if complete"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    today: date = date.today()
    page: Page = Page.objects.create(audit=audit, name="Incomplete page")
    completed_page: Page = Page.objects.create(audit=audit, name="Complete page", complete_date=today)

    form: AuditPageChecksForm = AuditPageChecksForm()
    form.fields["next_page"].queryset = Page.objects.all()

    choices = list(form.fields["next_page"].choices)

    assert len(choices) == 2
    assert choices[0][0].instance == page
    assert choices[0][1] == "Incomplete page"
    assert choices[1][0].instance == completed_page
    assert choices[1][1] == "Complete page ✓"
