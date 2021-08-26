"""
Test forms of cases app
"""
import pytest

from ..forms import CaseSearchForm

USER_CHOICES = [("", "-----"), ("none", "Unassigned")]


@pytest.mark.parametrize("fieldname", ["auditor", "reviewer"])
@pytest.mark.django_db
def test_case_search_form_user_field_includes_choice_of_unassigned(fieldname):
    """Tests if user choice field includes empty and unassigned options"""
    form: CaseSearchForm = CaseSearchForm(fieldname)
    assert fieldname in form.fields
    assert form.fields[fieldname].choices == USER_CHOICES
