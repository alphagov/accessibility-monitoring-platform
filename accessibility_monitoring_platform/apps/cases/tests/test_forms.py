"""
Test forms of cases app
"""

import pytest

from ..forms import CaseSearchForm
from ..models import ALL_CASE_STATUS_SEARCH_CHOICES, CASE_STATUS_UNKNOWN


@pytest.mark.django_db
def test_case_status_unknown_not_in_status_choices():
    """Tests Case status UNKNOWN has been removed from status choices"""

    form: CaseSearchForm = CaseSearchForm()

    assert len(form.fields["status"].choices) == len(ALL_CASE_STATUS_SEARCH_CHOICES)
    assert CASE_STATUS_UNKNOWN.value not in [
        value for value, _ in form.fields["status"].choices
    ]


@pytest.mark.django_db
def test_search_cases_choices_label_used():
    """Tests search cases choice labels, with test-type suffix used in form"""

    form: CaseSearchForm = CaseSearchForm()

    for test_type_label_suffix in ["(S)", "(D)", "(D&M)"]:
        assert (
            len(
                [
                    label
                    for _, label in form.fields["status"].choices
                    if label.endswith(test_type_label_suffix)
                ]
            )
            > 0
        )
