"""
Test utility functions of cases app
"""
import pytest

import csv
from dataclasses import dataclass
from datetime import date, datetime, timezone
import io
from typing import Any, Dict, List, Optional, Tuple

from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.http import HttpResponse
from django.http.request import QueryDict

from ...audits.models import Audit
from ...common.models import BOOLEAN_TRUE

from ..models import (
    Case,
    CaseEvent,
    Contact,
    CASE_EVENT_TYPE_CREATE,
    CASE_EVENT_AUDITOR,
    CASE_EVENT_CREATE_AUDIT,
    CASE_EVENT_READY_FOR_QA,
    CASE_EVENT_QA_AUDITOR,
    CASE_EVENT_APPROVE_REPORT,
    CASE_EVENT_READY_FOR_FINAL_DECISION,
    CASE_EVENT_CASE_COMPLETED,
    REPORT_APPROVED_STATUS_APPROVED,
    CASE_COMPLETED_NO_SEND,
)
from ..utils import (
    FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
    COLUMNS_FOR_EQUALITY_BODY,
    EXTRA_AUDIT_COLUMNS_FOR_EQUALITY_BODY,
    CASE_COLUMNS_FOR_EXPORT,
    CONTACT_COLUMNS_FOR_EXPORT,
    get_sent_date,
    filter_cases,
    ColumnAndFieldNames,
    format_model_field,
    format_contacts,
    replace_search_key_with_case_search,
    download_feedback_survey_cases,
    download_equality_body_cases,
    download_cases,
    record_case_event,
    build_edit_link_html,
)

ORGANISATION_NAME: str = "Organisation name one"
ORGANISATION_NAME_COMPLAINT: str = "Organisation name two"
ORGANISATION_NAME_ECNI: str = "Organisation name ecni"
ORGANISATION_NAME_EHRC: str = "Organisation name ehrc"

CONTACTS: List[Contact] = [
    Contact(
        name="Name 1",
        job_title="Job title 1",
        email="email1",
    ),
    Contact(
        name="Name 2",
        job_title="Job title 2",
        email="email2",
    ),
]

CSV_EXPORT_FILENAME: str = "cases_export.csv"
CONTACT_NOTES: str = "Contact notes"


@dataclass
class MockCase:
    """Mock of case for testing"""

    sent_date: str


@dataclass
class MockForm:
    """Mock of form for testing"""

    cleaned_data: Dict[str, str]


def decode_csv_response(response: HttpResponse) -> Tuple[List[str], List[List[str]]]:
    """Decode CSV HTTP response and break into column names and data"""
    content: str = response.content.decode("utf-8")
    cvs_reader: Any = csv.reader(io.StringIO(content))
    csv_body: List[List[str]] = list(cvs_reader)
    csv_header: List[str] = csv_body.pop(0)
    return csv_header, csv_body


def validate_csv_response(
    csv_header: List[str],
    csv_body: List[List[str]],
    expected_header: List[str],
    expected_first_data_row: List[str],
):
    """Validate csv header and body matches expected data"""
    assert csv_header == expected_header

    first_data_row: List[str] = csv_body[0]

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
    Case.objects.create(organisation_name=ORGANISATION_NAME)
    form: MockForm = MockForm(cleaned_data={"case_search": ORGANISATION_NAME})

    filtered_cases: List[Case] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == ORGANISATION_NAME


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
    Case.objects.create(organisation_name=ORGANISATION_NAME)
    Case.objects.create(
        organisation_name=ORGANISATION_NAME_COMPLAINT, is_complaint="yes"
    )
    form: MockForm = MockForm(cleaned_data={"is_complaint": is_complaint_filter})

    filtered_cases: List[Case] = list(filter_cases(form))

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
    Case.objects.create(
        organisation_name=ORGANISATION_NAME_ECNI, enforcement_body="ecni"
    )
    Case.objects.create(
        organisation_name=ORGANISATION_NAME_EHRC, enforcement_body="ehrc"
    )
    form: MockForm = MockForm(
        cleaned_data={"enforcement_body": enforcement_body_filter}
    )

    filtered_cases: List[Case] = list(filter_cases(form))  # type: ignore

    assert len(filtered_cases) == expected_number
    assert filtered_cases[0].organisation_name == expected_name


@pytest.mark.django_db
def test_cases_ordered_to_put_unassigned_first():
    """Test that case filtering returns unassigned cases first by default"""
    first_created: Case = Case.objects.create(
        organisation_name=ORGANISATION_NAME_ECNI, enforcement_body="ecni"
    )
    second_created: Case = Case.objects.create(
        organisation_name=ORGANISATION_NAME_EHRC, enforcement_body="ehrc"
    )
    form: MockForm = MockForm(cleaned_data={})

    filtered_cases: List[Case] = list(filter_cases(form))

    assert len(filtered_cases) == 2
    assert filtered_cases[0].organisation_name == second_created.organisation_name

    auditor: User = User.objects.create(
        username="new", first_name="New", last_name="User"
    )
    second_created.auditor = auditor
    second_created.save()

    filtered_cases: List[Case] = list(filter_cases(form))

    assert len(filtered_cases) == 2
    assert filtered_cases[0].organisation_name == first_created.organisation_name


def test_format_case_field_with_no_data():
    """
    Test that format_model_field returns empty string if no model instance
    """
    assert (
        format_model_field(
            model_instance=None,
            column=ColumnAndFieldNames(column_name="A", field_name="a"),
        )
        == ""
    )


@pytest.mark.parametrize(
    "column, case_value, expected_formatted_value",
    [
        (
            ColumnAndFieldNames(column_name="Test type", field_name="test_type"),
            "simplified",
            "Simplified",
        ),
        (
            ColumnAndFieldNames(
                column_name="Report sent on", field_name="report_sent_date"
            ),
            date(2020, 12, 31),
            "31/12/2020",
        ),
        (
            ColumnAndFieldNames(
                column_name="Enforcement recommendation",
                field_name="recommendation_for_enforcement",
            ),
            "no-further-action",
            "No further action",
        ),
        (
            ColumnAndFieldNames(
                column_name="Which equality body will check the case",
                field_name="enforcement_body",
            ),
            "ehrc",
            "EHRC",
        ),
    ],
)
def test_format_case_field(column, case_value, expected_formatted_value):
    """Test that case fields are formatted correctly"""
    case: Case = Case()
    setattr(case, column.field_name, case_value)
    assert expected_formatted_value == format_model_field(
        model_instance=case, column=column
    )


@pytest.mark.parametrize(
    "column, expected_formatted_value",
    [
        (
            ColumnAndFieldNames(column_name="Contact name", field_name=None),
            "Name 1\nName 2",
        ),
        (
            ColumnAndFieldNames(column_name="Job title", field_name=None),
            "Job title 1\nJob title 2",
        ),
        (
            ColumnAndFieldNames(column_name="Contact detail", field_name=None),
            "email1\nemail2",
        ),
    ],
)
def test_format_contacts(column, expected_formatted_value):
    """Test that contacts fields values are contatenated"""
    assert expected_formatted_value == format_contacts(contacts=CONTACTS, column=column)


@pytest.mark.parametrize(
    "query_dict, expected_dict",
    [
        (QueryDict(), {}),
        (QueryDict(query_string="query=apple"), {"query": "apple"}),
        (QueryDict(query_string="search=banana"), {"case_search": "banana"}),
    ],
)
def test_replace_search_key_with_case_search(
    query_dict: QueryDict, expected_dict: Dict[str, str]
):
    """
    Replace key search, if present, with case_search
    while converting QueryDict to dict.
    """
    assert replace_search_key_with_case_search(query_dict) == expected_dict


@pytest.mark.django_db
def test_download_feedback_survey_cases():
    """Test creation of CSV for feedback survey"""
    case: Case = Case.objects.create(
        compliance_email_sent_date=datetime(2022, 12, 16, tzinfo=timezone.utc),
        contact_notes=CONTACT_NOTES,
    )
    cases: List[Case] = [case]

    response: HttpResponse = download_feedback_survey_cases(
        cases=cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: List[str] = [
        column.column_name
        for column in FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT + CONTACT_COLUMNS_FOR_EXPORT
    ]
    expected_first_data_row: List[str] = [
        "1",
        "",
        "16/12/2022",
        "",
        CONTACT_NOTES,
        "No",
        "",
    ]

    validate_csv_response(
        csv_header=csv_header,
        csv_body=csv_body,
        expected_header=expected_header,
        expected_first_data_row=expected_first_data_row,
    )


@pytest.mark.django_db
def test_download_equality_body_cases():
    """Test creation of CSV for equality bodies"""
    case: Case = Case.objects.create()
    cases: List[Case] = [case]
    Audit.objects.create(
        case=case,
        archive_audit_retest_disproportionate_burden_notes="Audit for CSV export",
    )

    response: HttpResponse = download_equality_body_cases(
        cases=cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: List[str] = [
        column.column_name
        for column in COLUMNS_FOR_EQUALITY_BODY + EXTRA_AUDIT_COLUMNS_FOR_EQUALITY_BODY
    ]

    expected_first_data_row: List[str] = [
        "EHRC",
        "Simplified",
        "1",
        "",
        "",
        "",
        "No",
        "",
        "Not selected",
        "",
        "",
        "Not known",
        "",
        "Not selected",
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
        "n/a",
        "No claim",
        "",
        "No claim",
        "Audit for CSV export",
    ]

    validate_csv_response(
        csv_header=csv_header,
        csv_body=csv_body,
        expected_header=expected_header,
        expected_first_data_row=expected_first_data_row,
    )


@pytest.mark.django_db
def test_download_cases():
    """Test creation of CSV download of cases"""
    case: Case = Case.objects.create(
        created=datetime(2022, 12, 16, tzinfo=timezone.utc),
        contact_notes="Contact for CSV export",
    )
    cases: List[Case] = [case]
    Contact.objects.create(case=case, email="test@example.com")

    response: HttpResponse = download_cases(cases=cases, filename=CSV_EXPORT_FILENAME)

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: List[str] = [
        column.column_name
        for column in CASE_COLUMNS_FOR_EXPORT + CONTACT_COLUMNS_FOR_EXPORT
    ]

    expected_first_data_row: List[str] = [
        "1",
        "1",
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
        "Platform",
        "No",
        "",
        "",
        "",
        "",
        "Not selected",
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
        "Not selected",
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
        "Not selected",
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
        "",
        "",
        "False",
        "",
        "",
        "Unknown",
        "Contact for CSV export",
        "",
        "n/a",
        "test@example.com",
    ]

    validate_csv_response(
        csv_header=csv_header,
        csv_body=csv_body,
        expected_header=expected_header,
        expected_first_data_row=expected_first_data_row,
    )


@pytest.mark.parametrize(
    "new_case_params, old_case_params, event_type, message",
    [
        ({}, None, CASE_EVENT_TYPE_CREATE, "Created case"),
        (
            {"report_review_status": BOOLEAN_TRUE},
            {},
            CASE_EVENT_READY_FOR_QA,
            "Report ready to be reviewed changed from 'No' to 'Yes'",
        ),
        (
            {"report_approved_status": REPORT_APPROVED_STATUS_APPROVED},
            {},
            CASE_EVENT_APPROVE_REPORT,
            "Report approved changed from 'Not started' to 'Yes'",
        ),
        (
            {"is_ready_for_final_decision": BOOLEAN_TRUE},
            {},
            CASE_EVENT_READY_FOR_FINAL_DECISION,
            "Case ready for final decision changed from 'No' to 'Yes'",
        ),
        (
            {"case_completed": CASE_COMPLETED_NO_SEND},
            {},
            CASE_EVENT_CASE_COMPLETED,
            "Case completed changed from 'Case still in progress' to 'Case should not be sent to the equality body'",
        ),
    ],
)
@pytest.mark.django_db
def test_record_case_event(
    new_case_params: Dict, old_case_params: Dict, event_type: str, message: str
):
    """Test case events created"""
    user: User = User.objects.create()
    new_case: Case = Case.objects.create(**new_case_params)
    old_case: Optional[Case] = (
        None if old_case_params is None else Case.objects.create(**old_case_params)
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
    new_case: Case = Case.objects.create(auditor=new_auditor)
    old_case: Case = Case.objects.create(auditor=old_auditor)

    record_case_event(user=user, new_case=new_case, old_case=old_case)

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.all()
    assert case_events.count() == 1

    case_event = case_events[0]
    assert case_event.event_type == CASE_EVENT_AUDITOR
    assert case_event.message == "Auditor changed from Old User to New User"


@pytest.mark.django_db
def test_record_case_event_audit_create():
    """Test case event created on creation of an audit"""
    user: User = User.objects.create()
    new_case: Case = Case.objects.create()
    old_case: Case = Case.objects.create()
    Audit.objects.create(case=new_case)

    record_case_event(user=user, new_case=new_case, old_case=old_case)

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.all()
    assert case_events.count() == 1

    case_event = case_events[0]
    assert case_event.event_type == CASE_EVENT_CREATE_AUDIT
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
    new_case: Case = Case.objects.create(reviewer=new_reviewer)
    old_case: Case = Case.objects.create(reviewer=old_reviewer)

    record_case_event(user=user, new_case=new_case, old_case=old_case)

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.all()
    assert case_events.count() == 1

    case_event = case_events[0]
    assert case_event.event_type == CASE_EVENT_QA_AUDITOR
    assert case_event.message == "QA auditor changed from Old User to New User"


@pytest.mark.django_db
def test_build_edit_link_html():
    """Test building of edit link html for a case"""
    case: Case = Case.objects.create()

    assert (
        build_edit_link_html(case=case, url_name="cases:edit-test-results")
        == "<a href='/cases/1/edit-test-results/' class='govuk-link govuk-link--no-visited-state'>Edit</a>"
    )
