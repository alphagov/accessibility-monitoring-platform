"""
Test forms of cases app
"""

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from ...detailed.models import DetailedCase
from ...simplified.models import SimplifiedCase
from ..forms import CaseSearchForm, PreviousCaseURLForm
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


@pytest.mark.django_db
@patch("accessibility_monitoring_platform.apps.cases.forms.requests")
def test_clean_previous_case_url_detailed_valid(mock_requests):
    """Tests previous_case_url validation for valid detailed URL"""
    detailed_case: DetailedCase = DetailedCase.objects.create()
    mock_requests_response: MagicMock = MagicMock()
    mock_requests_response.status_code = 200
    mock_requests.head.return_value = mock_requests_response
    previous_case_path: str = reverse(
        "detailed:case-detail", kwargs={"pk": detailed_case.id}
    )
    previous_case_url: str = (
        f"https://platform.accessibility-monitoring.service.gov.uk{previous_case_path}"
    )
    form: PreviousCaseURLForm = PreviousCaseURLForm(
        data={"previous_case_url": previous_case_url}
    )

    assert form.is_valid() is True


@pytest.mark.django_db
@patch("accessibility_monitoring_platform.apps.cases.forms.requests")
def test_clean_previous_case_url_simplified_valid(mock_requests):
    """Tests previous_case_url validation for valid simplified URL"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    mock_requests_response: MagicMock = MagicMock()
    mock_requests_response.status_code = 200
    mock_requests.head.return_value = mock_requests_response
    previous_case_path: str = reverse(
        "simplified:case-detail", kwargs={"pk": simplified_case.id}
    )
    previous_case_url: str = (
        f"https://platform.accessibility-monitoring.service.gov.uk{previous_case_path}"
    )
    form: PreviousCaseURLForm = PreviousCaseURLForm(
        data={"previous_case_url": previous_case_url}
    )

    assert form.is_valid() is True
