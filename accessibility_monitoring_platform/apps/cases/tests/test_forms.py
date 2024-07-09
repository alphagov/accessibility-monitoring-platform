"""
Test forms of cases app
"""

from datetime import date
from typing import List, Tuple
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import Group, User

from ...audits.models import Audit
from ...common.models import Boolean
from ...reports.models import Report
from ...s3_read_write.models import S3Report
from ..forms import (
    CaseCloseUpdateForm,
    CaseFourWeekFollowupUpdateForm,
    CaseMetadataUpdateForm,
    CaseOneWeekFollowupFinalUpdateForm,
    CaseOneWeekFollowupUpdateForm,
    CasePublishReportUpdateForm,
    CaseSearchForm,
)
from ..models import Case

USER_CHOICES: List[Tuple[str, str]] = [("", "-----"), ("none", "Unassigned")]
FIRST_NAME: str = "Mock"
LAST_NAME: str = "User"
HOME_PAGE_URL: str = "https://example.com"
TODAY = date.today()


@pytest.mark.parametrize("fieldname", ["auditor", "reviewer"])
@pytest.mark.django_db
def test_case_search_form_user_field_includes_choice_of_unassigned(fieldname):
    """Tests if user choice field includes empty and unassigned options"""
    form: CaseSearchForm = CaseSearchForm()
    assert fieldname in form.fields
    assert form.fields[fieldname].choices == USER_CHOICES


@pytest.mark.parametrize("fieldname", ["auditor", "reviewer"])
@pytest.mark.django_db
def test_case_search_form_user_field_includes_historic_auditors(fieldname):
    """Tests if user choice field includes members of Historic auditor group"""
    group: Group = Group.objects.create(name="Historic auditor")
    user: User = User.objects.create(first_name=FIRST_NAME, last_name=LAST_NAME)
    group.user_set.add(user)
    expected_choices: List[Tuple[str, str]] = USER_CHOICES + [
        (user.id, f"{FIRST_NAME} {LAST_NAME}")
    ]

    form: CaseSearchForm = CaseSearchForm()
    assert fieldname in form.fields
    assert form.fields[fieldname].choices == expected_choices


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
    form: CaseMetadataUpdateForm = CaseMetadataUpdateForm(
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


@pytest.mark.django_db
def test_one_week_followup_hidden_when_report_ack():
    """
    Tests one week folloup fields are hidden when report has been
    acknowledged
    """
    case: Case = Case.objects.create()
    form: CaseOneWeekFollowupUpdateForm = CaseOneWeekFollowupUpdateForm(instance=case)

    hidden_fields: List[str] = [field.name for field in form.hidden_fields()]
    assert hidden_fields == ["version"]

    case.report_acknowledged_date = TODAY
    form: CaseOneWeekFollowupUpdateForm = CaseOneWeekFollowupUpdateForm(instance=case)
    hidden_fields: List[str] = [field.name for field in form.hidden_fields()]

    assert hidden_fields == [
        "version",
        "report_followup_week_1_sent_date",
        "report_followup_week_1_due_date",
        "one_week_followup_sent_to_email",
    ]


@pytest.mark.django_db
def test_four_week_followup_hidden_when_report_ack():
    """
    Tests four week folloup fields are hidden when report has been
    acknowledged
    """
    case: Case = Case.objects.create()
    form: CaseFourWeekFollowupUpdateForm = CaseFourWeekFollowupUpdateForm(instance=case)

    hidden_fields: List[str] = [field.name for field in form.hidden_fields()]
    assert hidden_fields == ["version"]

    case.report_acknowledged_date = TODAY
    form: CaseFourWeekFollowupUpdateForm = CaseFourWeekFollowupUpdateForm(instance=case)
    hidden_fields: List[str] = [field.name for field in form.hidden_fields()]

    assert hidden_fields == [
        "version",
        "report_followup_week_4_sent_date",
        "report_followup_week_4_due_date",
        "four_week_followup_sent_to_email",
    ]


@pytest.mark.django_db
def test_one_week_followup_final_hidden_when_12_week_cores_ack():
    """
    Tests four week folloup fields are hidden when 12-week correspondence
    has been acknowledged
    """
    case: Case = Case.objects.create()
    form: CaseOneWeekFollowupFinalUpdateForm = CaseOneWeekFollowupFinalUpdateForm(
        instance=case
    )

    hidden_fields: List[str] = [field.name for field in form.hidden_fields()]
    assert hidden_fields == ["version"]

    case.twelve_week_correspondence_acknowledged_date = TODAY
    form: CaseOneWeekFollowupFinalUpdateForm = CaseOneWeekFollowupFinalUpdateForm(
        instance=case
    )
    hidden_fields: List[str] = [field.name for field in form.hidden_fields()]

    assert hidden_fields == [
        "version",
        "twelve_week_1_week_chaser_sent_date",
        "twelve_week_1_week_chaser_due_date",
        "twelve_week_1_week_chaser_sent_to_email",
    ]


@pytest.mark.parametrize(
    "case_completed, expected_error_message",
    [
        (Case.CaseCompleted.NO_DECISION, ""),
        (Case.CaseCompleted.COMPLETE_NO_SEND, ""),
        (
            Case.CaseCompleted.COMPLETE_SEND,
            "Ensure all the required fields are complete before you close the case to send to the equalities body",
        ),
    ],
)
@pytest.mark.django_db
def test_clean_case_close_form(case_completed, expected_error_message):
    """Tests case checked for missing data only when being sent to equality body"""

    case: Case = Case.objects.create()
    form: CaseCloseUpdateForm = CaseCloseUpdateForm(
        data={
            "version": case.version,
            "case_completed": case_completed,
        },
        instance=case,
    )

    if expected_error_message:
        assert not form.is_valid()
        assert form.errors == {"__all__": [expected_error_message]}
    else:
        assert form.is_valid()


@pytest.mark.django_db
def test_publish_report_form_hides_fields_unless_report_has_been_published():
    """
    Tests publish report form hides its complete date field unless report has been published
    """
    case: Case = Case.objects.create()
    form: CasePublishReportUpdateForm = CasePublishReportUpdateForm(instance=case)

    hidden_fields: List[str] = [field.name for field in form.hidden_fields()]
    assert hidden_fields == ["version", "publish_report_complete_date"]

    Audit.objects.create(case=case)
    Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)
    hidden_fields: List[str] = [field.name for field in form.hidden_fields()]
    assert hidden_fields == ["version", "publish_report_complete_date"]

    case.report_review_status = Boolean.YES
    form: CasePublishReportUpdateForm = CasePublishReportUpdateForm(instance=case)
    hidden_fields: List[str] = [field.name for field in form.hidden_fields()]
    assert hidden_fields == ["version", "publish_report_complete_date"]

    case.report_approved_status = Case.ReportApprovedStatus.APPROVED
    form: CasePublishReportUpdateForm = CasePublishReportUpdateForm(instance=case)
    hidden_fields: List[str] = [field.name for field in form.hidden_fields()]
    assert hidden_fields == ["version"]
