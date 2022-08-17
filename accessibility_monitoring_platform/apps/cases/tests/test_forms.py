"""
Test forms of cases app
"""
from unittest.mock import MagicMock, patch
import pytest
from typing import List, Tuple

from ..forms import CaseSearchForm, CaseDetailUpdateForm
from ..models import Case

USER_CHOICES: List[Tuple[str, str]] = [("", "-----"), ("none", "Unassigned")]
HOME_PAGE_URL: str = "https://example.com"


@pytest.mark.parametrize("fieldname", ["auditor", "reviewer"])
@pytest.mark.django_db
def test_case_search_form_user_field_includes_choice_of_unassigned(fieldname):
    """Tests if user choice field includes empty and unassigned options"""
    form: CaseSearchForm = CaseSearchForm()
    assert fieldname in form.fields
    assert form.fields[fieldname].choices == USER_CHOICES  # type: ignore


@pytest.mark.parametrize(
    "testing_methodology, report_methodology, expected_valid",
    [
        ("platform", "platform", True),
        ("spreadsheet", "platform", False),
        ("platform", "odt", True),
        ("spreadsheet", "odt", True),
    ],
)
@pytest.mark.django_db
def test_case_report_detail_update_form_methodology_validation(
    testing_methodology, report_methodology, expected_valid
):
    """Tests testing and report methodology cross-field validation"""
    case: Case = Case.objects.create()
    form: CaseDetailUpdateForm = CaseDetailUpdateForm(
        data={
            "version": case.version,
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "testing_methodology": testing_methodology,
            "report_methodology": report_methodology,
        },
        instance=case,
    )

    if expected_valid:
        assert form.is_valid()
    else:
        assert not form.is_valid()
        assert form.errors == {
            "testing_methodology": [
                "Testing methodology has to be platform for reporting methodology to be platform",
            ],
            "report_methodology": [
                "For reporting methodology to be platform, testing methodology has to be platform",
            ],
        }


@pytest.mark.parametrize(
    "previous_case_url, requests_status, expected_error_message",
    [
        ("", 200, ""),
        ("https://platform.gov.uk/cases/1/view", 200, ""),
        (
            "https://platform.gov.uk/cases/1/view",
            404,
            "Previous case URL does not exist",
        ),
        (
            "https://platform.gov.uk/wrong-path/1/view",
            200,
            "Previous case URL did not contain case id",
        ),
        (
            "https://platform.gov.uk/cases/99/view",
            200,
            "Previous case not found in platform",
        ),
        (
            "https://platform.gov.uk/cases/not-an-id/view",
            200,
            "Previous case not found in platform",
        ),
    ],
)
@pytest.mark.django_db
@patch("accessibility_monitoring_platform.apps.cases.forms.requests")
def test_clean_previous_case_url(
    mock_requests, previous_case_url, requests_status, expected_error_message
):
    """Tests previous_case_url validation"""
    mock_requests_response: MagicMock = MagicMock()
    mock_requests_response.status_code = requests_status
    mock_requests.head.return_value = mock_requests_response

    case: Case = Case.objects.create()
    form: CaseDetailUpdateForm = CaseDetailUpdateForm(
        data={
            "version": case.version,
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "previous_case_url": previous_case_url,
        },
        instance=case,
    )

    if expected_error_message:
        assert not form.is_valid()
        assert form.errors == {
            "previous_case_url": [expected_error_message],
        }
    else:
        assert form.is_valid()
