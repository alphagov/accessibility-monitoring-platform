"""
Test utility functions of cases app
"""

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.urls import reverse

from ...audits.models import Audit, Retest
from ...cases.utils import CaseDetailSection
from ...common.models import Boolean
from ...common.sitemap import Sitemap
from ...common.tests.test_utils import decode_csv_response, validate_csv_response
from ..csv_export import (
    SIMPLIFIED_CASE_COLUMNS_FOR_EXPORT,
    SIMPLIFIED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
)
from ..models import (
    CaseCompliance,
    CaseEvent,
    Contact,
    SimplifiedCase,
    SimplifiedEventHistory,
)
from ..utils import (
    build_edit_link_html,
    create_case_and_compliance,
    download_simplified_cases,
    download_simplified_feedback_survey_cases,
    get_email_template_context,
    get_simplified_case_detail_sections,
    record_case_event,
    record_simplified_model_create_event,
    record_simplified_model_update_event,
)

ORGANISATION_NAME: str = "Organisation name one"
ORGANISATION_NAME_COMPLAINT: str = "Organisation name two"
ORGANISATION_NAME_ECNI: str = "Organisation name ecni"
ORGANISATION_NAME_EHRC: str = "Organisation name ehrc"
ORGANISATION_NAME_NO_FURTHER_ACTION: str = "Organisation name no further action"
ORGANISATION_NAME_FOR_ENFORCEMENT: str = "Organisation name for enforcement"
ORGANISATION_NAME_NOT_SELECTED: str = "Organisation name not selected"
CASE_NUMBER: int = 99

CSV_EXPORT_FILENAME: str = "cases_export.csv"

PAST_DATE: date = date(1900, 1, 1)
TODAYS_DATE: date = date.today()

DOMAIN: str = "domain.com"
HOME_PAGE_URL: str = f"https://{DOMAIN}"
ORGANISATION_NAME: str = "Organisation name"
PSB_LOCATION: str = "England"
SECTOR_NAME: str = "Sector name"
PARENTAL_ORGANISATION_NAME: str = "Parent organisation"
WEBSITE_NAME: str = "Website name"
SUBCATEGORY_NAME: str = "Sub-category name"
CASE_IDENTIFIER: str = "#S-1"
SIMPLIFIED_CONTACT_NOTES: str = "Simplified case contact notes"


@dataclass
class MockCase:
    """Mock of case for testing"""

    sent_date: str


@dataclass
class MockForm:
    """Mock of form for testing"""

    cleaned_data: dict[str, str]


@pytest.mark.parametrize(
    "new_case_params, old_case_params, event_type, message",
    [
        ({}, None, CaseEvent.EventType.CREATE, "Created case"),
        (
            {"report_review_status": Boolean.YES},
            {},
            CaseEvent.EventType.READY_FOR_QA,
            "Report ready to be reviewed changed from 'No' to 'Yes'",
        ),
        (
            {"report_approved_status": SimplifiedCase.ReportApprovedStatus.APPROVED},
            {},
            CaseEvent.EventType.APPROVE_REPORT,
            "QA approval changed from 'Not started' to 'Yes'",
        ),
        (
            {"is_ready_for_final_decision": Boolean.YES},
            {},
            CaseEvent.EventType.READY_FOR_FINAL_DECISION,
            "Case ready for final decision changed from 'No' to 'Yes'",
        ),
        (
            {"case_completed": SimplifiedCase.CaseCompleted.COMPLETE_NO_SEND},
            {},
            CaseEvent.EventType.CASE_COMPLETED,
            "Case completed changed from 'Case still in progress' to 'Case should not be sent to the equality body'",
        ),
    ],
)
@pytest.mark.django_db
def test_record_case_event(
    new_case_params: dict, old_case_params: dict, event_type: str, message: str
):
    """Test case events created"""
    user: User = User.objects.create()
    new_case: SimplifiedCase = SimplifiedCase.objects.create(**new_case_params)
    old_case: SimplifiedCase | None = (
        None
        if old_case_params is None
        else SimplifiedCase.objects.create(**old_case_params)
    )

    record_case_event(user=user, new_case=new_case, old_case=old_case)

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.all()
    assert case_events.count() == 1

    case_event = case_events[0]
    assert case_event.event_type == event_type
    assert case_event.message == message


@pytest.mark.django_db
def test_record_case_event_auditor_change():
    """Test case event created on change of auditor"""
    user: User = User.objects.create()
    new_auditor: User = User.objects.create(
        username="new", first_name="New", last_name="User"
    )
    old_auditor: User = User.objects.create(
        username="old", first_name="Old", last_name="User"
    )
    new_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=new_auditor)
    old_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=old_auditor)

    record_case_event(user=user, new_case=new_case, old_case=old_case)

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.all()
    assert case_events.count() == 1

    case_event = case_events[0]
    assert case_event.event_type == CaseEvent.EventType.AUDITOR
    assert case_event.message == "Auditor changed from Old User to New User"


@pytest.mark.django_db
def test_record_case_event_audit_create():
    """Test case event created on creation of an audit"""
    user: User = User.objects.create()
    new_case: SimplifiedCase = SimplifiedCase.objects.create()
    old_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=new_case)

    record_case_event(user=user, new_case=new_case, old_case=old_case)

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.all()
    assert case_events.count() == 1

    case_event = case_events[0]
    assert case_event.event_type == CaseEvent.EventType.CREATE_AUDIT
    assert case_event.message == "Start of test"


@pytest.mark.django_db
def test_record_case_event_reviewer_change():
    """Test case event created on change of reviewer"""
    user: User = User.objects.create()
    new_reviewer: User = User.objects.create(
        username="new", first_name="New", last_name="User"
    )
    old_reviewer: User = User.objects.create(
        username="old", first_name="Old", last_name="User"
    )
    new_case: SimplifiedCase = SimplifiedCase.objects.create(reviewer=new_reviewer)
    old_case: SimplifiedCase = SimplifiedCase.objects.create(reviewer=old_reviewer)

    record_case_event(user=user, new_case=new_case, old_case=old_case)

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.all()
    assert case_events.count() == 1

    case_event = case_events[0]
    assert case_event.event_type == CaseEvent.EventType.QA_AUDITOR
    assert case_event.message == "QA auditor changed from Old User to New User"


@pytest.mark.django_db
def test_build_edit_link_html():
    """Test building of edit link html for a case"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert (
        build_edit_link_html(
            simplified_case=simplified_case, url_name="simplified:edit-test-results"
        )
        == "<a href='/simplified/1/edit-test-results/' class='govuk-link govuk-link--no-visited-state'>Edit</a>"
    )


@pytest.mark.django_db
def test_create_case_and_compliance_no_args():
    """Test cretaion of case and compliance with no arguments"""
    simplified_case: SimplifiedCase = create_case_and_compliance()

    assert isinstance(simplified_case, SimplifiedCase)
    assert isinstance(simplified_case.compliance, CaseCompliance)


@pytest.mark.django_db
def test_create_case_and_compliance():
    """Test cretaion of case and compliance with mix of arguments"""
    simplified_case: SimplifiedCase = create_case_and_compliance(
        organisation_name=ORGANISATION_NAME,
        website_compliance_state_12_week="compliant",
    )

    assert simplified_case.organisation_name == ORGANISATION_NAME
    assert simplified_case.compliance.website_compliance_state_12_week == "compliant"


@pytest.mark.django_db
def test_record_model_create_event():
    """Test creation of model create event"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    user: User = User.objects.create()
    record_simplified_model_create_event(
        user=user, model_object=user, simplified_case=simplified_case
    )

    content_type: ContentType = ContentType.objects.get_for_model(User)
    event: SimplifiedEventHistory = SimplifiedEventHistory.objects.get(
        content_type=content_type, object_id=user.id, simplified_case=simplified_case
    )

    assert event.event_type == SimplifiedEventHistory.Type.CREATE

    difference_dict: dict[str, Any] = json.loads(event.difference)

    assert "last_login" in difference_dict
    assert difference_dict["last_login"] is None
    assert "is_active" in difference_dict
    assert difference_dict["is_active"] is True
    assert "is_staff" in difference_dict
    assert difference_dict["is_staff"] is False


@pytest.mark.django_db
def test_record_model_update_event():
    """Test creation of model update event"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    user: User = User.objects.create()
    user.first_name = "Changed"
    record_simplified_model_update_event(
        user=user, model_object=user, simplified_case=simplified_case
    )

    content_type: ContentType = ContentType.objects.get_for_model(User)
    event: SimplifiedEventHistory = SimplifiedEventHistory.objects.get(
        content_type=content_type, object_id=user.id, simplified_case=simplified_case
    )

    assert event.event_type == SimplifiedEventHistory.Type.UPDATE
    assert event.difference == '{"first_name": " -> Changed"}'


@pytest.mark.django_db
def test_download_cases_simplified():
    """Test creation of CSV download of simplified cases"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        contact_notes="Contact for CSV export",
    )
    simplified_case.created = datetime(2022, 12, 16, tzinfo=timezone.utc)
    simplified_case.save()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_case.update_case_status()
    simplified_cases: list[SimplifiedCase] = [simplified_case]
    Contact.objects.create(simplified_case=simplified_case, email="test@example.com")

    response: StreamingHttpResponse = download_simplified_cases(
        simplified_cases=simplified_cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: list[str] = [
        column.column_header for column in SIMPLIFIED_CASE_COLUMNS_FOR_EXPORT
    ]

    expected_first_data_row: list[str] = [
        "1",
        "2",
        "",
        "16/12/2022",
        "Unassigned case",
        "",
        "Simplified",
        "",
        "",
        "",
        "Unknown",
        "",
        "EHRC",
        "No",
        "",
        "",
        "",
        "",
        "Not assessed",
        "",
        "Not known",
        "",
        "",
        "",
        "",
        "",
        "No",
        "",
        "Not started",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "No",
        "",
        "",
        "",
        "",
        "Not applicable or organisation responded to 12-week update",
        "",
        "",
        "",
        "",
        "",
        "No",
        "",
        "Not known",
        "",
        "",
        "Not known",
        "",
        "",
        "Not assessed",
        "",
        "",
        "Not selected",
        "",
        "",
        "Case still in progress",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "No",
        "No (or holding)",
        "",
        "",
        "False",
        "",
        "",
        "Unknown",
        "Contact for CSV export",
        "",
        "n/a",
        "",
        "",
        "",
        "test@example.com",
    ]

    validate_csv_response(
        csv_header=csv_header,
        csv_body=csv_body,
        expected_header=expected_header,
        expected_first_data_row=expected_first_data_row,
    )


@pytest.mark.django_db
def test_download_feedback_survey_cases():
    """Test creation of CSV for feedback survey"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        compliance_email_sent_date=datetime(2022, 12, 16, tzinfo=timezone.utc),
        contact_notes=SIMPLIFIED_CONTACT_NOTES,
    )
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_cases: list[SimplifiedCase] = [simplified_case]

    response: StreamingHttpResponse = download_simplified_feedback_survey_cases(
        cases=simplified_cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: list[str] = [
        column.column_header for column in SIMPLIFIED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT
    ]
    expected_first_data_row: list[str] = [
        "1",  # Case no.
        "",  # Website name
        "",  # Organisation name
        "16/12/2022",  # Closing the case date
        "Not selected",  # Enforcement recommendation
        "",  # Enforcement recommendation notes
        "Not assessed",  # statement_compliance_state_12_week
        "",  # Contact email
        SIMPLIFIED_CONTACT_NOTES,  # Contact notes
        "No",  # Feedback survey sent
        "",  # Compliance decision email sent to
    ]

    validate_csv_response(
        csv_header=csv_header,
        csv_body=csv_body,
        expected_header=expected_header,
        expected_first_data_row=expected_first_data_row,
    )


@pytest.mark.django_db
def test_get_simplified_case_detail_sections(rf):
    """Test get_simplified_case_detail_sections builds list of detail sections"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )
    request: HttpRequest = rf.get(
        reverse("simplified:case-view-and-search", kwargs={"pk": simplified_case.id}),
    )
    sitemap: Sitemap = Sitemap(request=request)

    sections: list[CaseDetailSection] = get_simplified_case_detail_sections(
        simplified_case=simplified_case, sitemap=sitemap
    )

    assert sections[0].pages[0].display_fields is not None
    assert sections[0].pages[0].display_fields[2].value == ORGANISATION_NAME


@pytest.mark.django_db
def test_get_email_template_context_new_case():
    """Test get_email_template_context for new Case"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    email_template_context: dict[str, Any] = get_email_template_context(
        simplified_case=simplified_case
    )

    assert "12_weeks_from_today" in email_template_context
    assert email_template_context["case"] == simplified_case
    assert email_template_context["retest"] is None


@pytest.mark.django_db
def test_get_email_template_context_12_weeks_from_today():
    """Test get_email_template_context 12_weeks_from_today present and correct"""
    with patch(
        "accessibility_monitoring_platform.apps.simplified.utils.date"
    ) as mock_date:
        mock_date.today.return_value = date(2023, 2, 1)
        simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
        email_template_context: dict[str, Any] = get_email_template_context(
            simplified_case=simplified_case
        )

        assert "12_weeks_from_today" in email_template_context
        assert email_template_context["12_weeks_from_today"] == date(2023, 4, 26)


@pytest.mark.django_db
def test_get_email_template_context_with_audit():
    """Test get_email_template_context for Case with test"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=simplified_case)
    email_template_context: dict[str, Any] = get_email_template_context(
        simplified_case=simplified_case
    )

    assert email_template_context["case"] == simplified_case
    assert email_template_context["retest"] is None

    assert "issues_tables" in email_template_context
    assert "retest_issues_tables" in email_template_context


@pytest.mark.django_db
def test_get_email_template_context_with_retest():
    """Test get_email_template_context for Case with equality body retest"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    retest: Retest = Retest.objects.create(simplified_case=simplified_case)
    email_template_context: dict[str, Any] = get_email_template_context(
        simplified_case=simplified_case
    )

    assert email_template_context["case"] == simplified_case
    assert email_template_context["retest"] == retest
