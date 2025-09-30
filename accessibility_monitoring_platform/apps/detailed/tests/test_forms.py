"""
Test forms of detailed app
"""

from unittest.mock import MagicMock, patch

import pytest

from ..forms import DetailedCaseMetadataUpdateForm
from ..models import DetailedCase

HOME_PAGE_URL: str = "https://example.com"


@pytest.mark.parametrize(
    "previous_case_url, requests_status, expected_error_message",
    [
        ("", 200, ""),
        ("https://platform.gov.uk/detailed/1/case-detail", 200, ""),
        (
            "https://platform.gov.uk/detailed/1/case-detail",
            404,
            "Previous case URL does not exist",
        ),
        (
            "https://platform.gov.uk/wrong-path/1/case-detail",
            200,
            "Previous case URL did not contain case id",
        ),
        (
            "https://platform.gov.uk/detailed/99/case-detail",
            200,
            "Previous case not found in platform",
        ),
        (
            "https://platform.gov.uk/detailed/not-an-id/case-detail",
            200,
            "Previous case URL did not contain case id",
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

    detailed_case: DetailedCase = DetailedCase.objects.create()
    form: DetailedCaseMetadataUpdateForm = DetailedCaseMetadataUpdateForm(
        data={
            "version": detailed_case.version,
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "previous_case_url": previous_case_url,
        },
        instance=detailed_case,
    )

    if expected_error_message:
        assert not form.is_valid()
        assert form.errors == {
            "previous_case_url": [expected_error_message],
        }
    else:
        assert form.is_valid()
