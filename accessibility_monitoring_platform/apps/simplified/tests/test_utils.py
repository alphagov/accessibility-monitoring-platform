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
from django.http.request import QueryDict

from ...audits.models import Audit
from ...common.models import Boolean, Sector, SubCategory
from ..models import CaseCompliance, CaseEvent, SimplifiedCase, SimplifiedEventHistory
from ..utils import (
    build_edit_link_html,
    create_case_and_compliance,
    filter_cases,
    get_sent_date,
    record_case_event,
    record_simplified_model_create_event,
    record_simplified_model_update_event,
    replace_search_key_with_case_search,
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
    "date_on_form, date_on_db, expected_date",
    [
        ("form_date", "db_date", "db_date"),
        (None, "db_date", None),
        ("form_date", None, "form_date"),
    ],
)
def test_get_sent_date(date_on_form, date_on_db, expected_date):
    mock_form: MockForm = MockForm(cleaned_data={"sent_date": date_on_form})
    mock_case: MockCase = MockCase(sent_date=date_on_db)

    assert (
        get_sent_date(
            form=mock_form, case_from_db=mock_case, sent_date_name="sent_date"
        )
        == expected_date
    )


@pytest.mark.django_db
def test_case_filtered_by_search_string():
    """Test that searching for cases is reflected in the queryset"""
    SimplifiedCase.objects.create(organisation_name=ORGANISATION_NAME)
    form: MockForm = MockForm(cleaned_data={"case_search": ORGANISATION_NAME})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == ORGANISATION_NAME


@pytest.mark.django_db
def test_case_filtered_by_case_number_search_string():
    """Test that searching for case by number is reflected in the queryset"""
    SimplifiedCase.objects.create(case_number=CASE_NUMBER)
    form: MockForm = MockForm(cleaned_data={"case_search": str(CASE_NUMBER)})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].case_number == CASE_NUMBER


@pytest.mark.django_db
def test_case_filtered_by_status():
    """Test that filtering cases by status is reflected in the queryset"""
    SimplifiedCase.objects.create(organisation_name=ORGANISATION_NAME)
    form: MockForm = MockForm(cleaned_data={"status": "unassigned-case"})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == ORGANISATION_NAME


@pytest.mark.parametrize(
    "recommendation_for_enforcement_filter, expected_number, expected_name",
    [
        ("", 3, ORGANISATION_NAME_NOT_SELECTED),
        ("no-further-action", 1, ORGANISATION_NAME_NO_FURTHER_ACTION),
        ("other", 1, ORGANISATION_NAME_FOR_ENFORCEMENT),
        ("unknown", 1, ORGANISATION_NAME_NOT_SELECTED),
    ],
)
@pytest.mark.django_db
def test_case_filtered_by_recommendation_for_enforcement(
    recommendation_for_enforcement_filter, expected_number, expected_name
):
    """
    Test that filtering by recommendation for enforcement is reflected in the queryset
    """
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_NO_FURTHER_ACTION,
        recommendation_for_enforcement="no-further-action",
    )
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_FOR_ENFORCEMENT,
        recommendation_for_enforcement="other",
    )
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_NOT_SELECTED,
        recommendation_for_enforcement="unknown",
    )
    form: MockForm = MockForm(
        cleaned_data={
            "recommendation_for_enforcement": recommendation_for_enforcement_filter
        }
    )

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))  # type: ignore

    assert len(filtered_cases) == expected_number
    assert filtered_cases[0].organisation_name == expected_name


@pytest.mark.parametrize(
    "is_complaint_filter, expected_number, expected_name",
    [
        ("", 2, ORGANISATION_NAME_COMPLAINT),
        ("no", 1, ORGANISATION_NAME),
        ("yes", 1, ORGANISATION_NAME_COMPLAINT),
    ],
)
@pytest.mark.django_db
def test_case_filtered_by_is_complaint(
    is_complaint_filter, expected_number, expected_name
):
    """Test that filtering by complaint is reflected in the queryset"""
    SimplifiedCase.objects.create(organisation_name=ORGANISATION_NAME)
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_COMPLAINT, is_complaint="yes"
    )
    form: MockForm = MockForm(cleaned_data={"is_complaint": is_complaint_filter})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == expected_number
    assert filtered_cases[0].organisation_name == expected_name


@pytest.mark.parametrize(
    "enforcement_body_filter, expected_number, expected_name",
    [
        ("", 2, ORGANISATION_NAME_EHRC),
        ("ehrc", 1, ORGANISATION_NAME_EHRC),
        ("ecni", 1, ORGANISATION_NAME_ECNI),
    ],
)
@pytest.mark.django_db
def test_case_filtered_by_enforcement_body(
    enforcement_body_filter, expected_number, expected_name
):
    """Test that filtering by enforcement body is reflected in the queryset"""
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_ECNI, enforcement_body="ecni"
    )
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_EHRC, enforcement_body="ehrc"
    )
    form: MockForm = MockForm(
        cleaned_data={"enforcement_body": enforcement_body_filter}
    )

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))  # type: ignore

    assert len(filtered_cases) == expected_number
    assert filtered_cases[0].organisation_name == expected_name


@pytest.mark.django_db
def test_case_filtered_by_sector():
    """Test that filtering by sector is reflected in the queryset"""
    sector: Sector = Sector.objects.create()
    SimplifiedCase.objects.create(organisation_name=ORGANISATION_NAME, sector=sector)
    form: MockForm = MockForm(cleaned_data={"sector": sector})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == ORGANISATION_NAME


@pytest.mark.django_db
def test_case_filtered_by_subcategory():
    """Test that filtering by subcategory is reflected in the queryset"""
    subcategory: SubCategory = SubCategory.objects.create()
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME, subcategory=subcategory
    )
    form: MockForm = MockForm(cleaned_data={"subcategory": subcategory})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == ORGANISATION_NAME


@pytest.mark.django_db
def test_cases_ordered_to_put_unassigned_first():
    """Test that case filtering returns unassigned cases first by default"""
    first_created: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_ECNI, enforcement_body="ecni"
    )
    second_created: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_EHRC, enforcement_body="ehrc"
    )
    form: MockForm = MockForm(cleaned_data={})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 2
    assert filtered_cases[0].organisation_name == second_created.organisation_name

    auditor: User = User.objects.create(
        username="new", first_name="New", last_name="User"
    )
    second_created.auditor = auditor
    second_created.save()

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 2
    assert filtered_cases[0].organisation_name == first_created.organisation_name


@pytest.mark.parametrize(
    "query_dict, expected_dict",
    [
        (QueryDict(), {}),
        (QueryDict(query_string="query=apple"), {"query": "apple"}),
        (QueryDict(query_string="search=banana"), {"case_search": "banana"}),
    ],
)
def test_replace_search_key_with_case_search(
    query_dict: QueryDict, expected_dict: dict[str, str]
):
    """
    Replace key search, if present, with case_search
    while converting QueryDict to dict.
    """
    assert replace_search_key_with_case_search(query_dict) == expected_dict


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
    Audit.objects.create(case=new_case)

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
    case: SimplifiedCase = SimplifiedCase.objects.create()

    assert (
        build_edit_link_html(case=case, url_name="simplified:edit-test-results")
        == "<a href='/cases/1/edit-test-results/' class='govuk-link govuk-link--no-visited-state'>Edit</a>"
    )


@pytest.mark.django_db
def test_create_case_and_compliance_no_args():
    """Test cretaion of case and compliance with no arguments"""
    case: SimplifiedCase = create_case_and_compliance()

    assert isinstance(case, SimplifiedCase)
    assert isinstance(case.compliance, CaseCompliance)


@pytest.mark.django_db
def test_create_case_and_compliance():
    """Test cretaion of case and compliance with mix of arguments"""
    case: SimplifiedCase = create_case_and_compliance(
        organisation_name=ORGANISATION_NAME,
        website_compliance_state_12_week="compliant",
    )

    assert case.organisation_name == ORGANISATION_NAME
    assert case.compliance.website_compliance_state_12_week == "compliant"


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
