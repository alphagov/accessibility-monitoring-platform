"""
Test forms of cases app
"""

import pytest

from ..forms import CaseSearchForm
from ..models import ALL_CASE_STATUS_CHOICES, CASE_STATUS_UNKNOWN


@pytest.mark.django_db
def test_case_status_unknown_not_in_status_choices():
    """Tests Case status UNKNOWN has been removed from status choices"""

    form: CaseSearchForm = CaseSearchForm()

    assert len(form.fields["status"].choices) == len(ALL_CASE_STATUS_CHOICES)
    assert CASE_STATUS_UNKNOWN.value not in [
        value for value, _ in form.fields["status"].choices
    ]
