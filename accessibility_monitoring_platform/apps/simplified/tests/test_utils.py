"""
Test utility functions of cases app
"""

import json
from dataclasses import dataclass
from typing import Any

import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet

from ...audits.models import Audit
from ...common.models import Boolean
from ..models import CaseCompliance, CaseEvent, SimplifiedCase, SimplifiedEventHistory
from ..utils import (
    build_edit_link_html,
    create_case_and_compliance,
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


@dataclass
class MockCase:
    """Mock of case for testing"""

    sent_date: str


@dataclass
class MockForm:
    """Mock of form for testing"""

    cleaned_data: dict[str, str]


def validate_csv_response(
    csv_header: list[str],
    csv_body: list[list[str]],
    expected_header: list[str],
    expected_first_data_row: list[str],
):
    """Validate csv header and body matches expected data"""
    assert csv_header == expected_header

    first_data_row: list[str] = csv_body[0]

    for position in range(len(first_data_row)):
        assert (
            first_data_row[position] == expected_first_data_row[position]
        ), f"Data mismatch on column {position}: {expected_header[position]}"

    assert first_data_row == expected_first_data_row


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
    user: User = User.objects.create()
    record_simplified_model_create_event(user=user, model_object=user)

    content_type: ContentType = ContentType.objects.get_for_model(User)
    event: SimplifiedEventHistory = SimplifiedEventHistory.objects.get(
        content_type=content_type, object_id=user.id
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
    user: User = User.objects.create()
    user.first_name = "Changed"
    record_simplified_model_update_event(user=user, model_object=user)

    content_type: ContentType = ContentType.objects.get_for_model(User)
    event: SimplifiedEventHistory = SimplifiedEventHistory.objects.get(
        content_type=content_type, object_id=user.id
    )

    assert event.event_type == SimplifiedEventHistory.Type.UPDATE
    assert event.difference == '{"first_name": " -> Changed"}'
