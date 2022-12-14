"""
Test forms of cases app
"""
from unittest.mock import MagicMock, patch
import pytest
from typing import List, Tuple

from django.contrib.auth.models import Group, User

from ..forms import CaseSearchForm, CaseDetailUpdateForm
from ..models import Case

USER_CHOICES: List[Tuple[str, str]] = [("", "-----"), ("none", "Unassigned")]
FIRST_NAME: str = "Mock"
LAST_NAME: str = "User"
HOME_PAGE_URL: str = "https://example.com"


@pytest.mark.parametrize("fieldname", ["auditor", "reviewer"])
@pytest.mark.django_db
def test_case_search_form_user_field_includes_choice_of_unassigned(fieldname):
    """Tests if user choice field includes empty and unassigned options"""
    form: CaseSearchForm = CaseSearchForm()
    assert fieldname in form.fields
    assert form.fields[fieldname].choices == USER_CHOICES  # type: ignore


@pytest.mark.parametrize("fieldname", ["auditor", "reviewer"])
@pytest.mark.django_db
def test_case_search_form_user_field_includes_historic_auditors(fieldname):
    """Tests if user choice field includes members of Historic auditor group"""
    group: Group = Group.objects.create(name="Historic auditor")
    user: User = User.objects.create(first_name=FIRST_NAME, last_name=LAST_NAME)
    group.user_set.add(user)  # type: ignore
    expected_choices: List[Tuple[str, str]] = USER_CHOICES + [
        (user.id, f"{FIRST_NAME} {LAST_NAME}")  # type: ignore
    ]

    form: CaseSearchForm = CaseSearchForm()
    assert fieldname in form.fields
    assert form.fields[fieldname].choices == expected_choices  # type: ignore


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
