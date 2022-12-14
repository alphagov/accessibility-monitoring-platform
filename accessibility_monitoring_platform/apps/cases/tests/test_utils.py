"""
Test utility functions of cases app
"""
import pytest

import csv
from dataclasses import dataclass
from datetime import date
import io
from typing import Any, Dict, List, Tuple

from django.http import HttpResponse
from django.http.request import QueryDict

from ..models import Case, Contact
from ..utils import (
    get_sent_date,
    filter_cases,
    ColumnAndFieldNames,
    format_model_field,
    format_contacts,
    replace_search_key_with_case_search,
    download_equality_body_cases,
    download_cases,
)

ORGANISATION_NAME: str = "Organisation name one"
ORGANISATION_NAME_COMPLAINT: str = "Organisation name two"

CONTACTS: List[Contact] = [
    Contact(
        name="Name 1",
        job_title="Job title 1",
        email="email1",
        notes="notes1",
    ),
    Contact(
        name="Name 2",
        job_title="Job title 2",
        email="email2",
        notes="notes2",
    ),
]

CSV_EXPORT_FILENAME: str = "cases_export.csv"


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
        get_sent_date(form=mock_form, case_from_db=mock_case, sent_date_name="sent_date")  # type: ignore
        == expected_date
    )


@pytest.mark.django_db
def test_case_filtered_by_search_string():
    """Test that searching for cases is reflected in the queryset"""
    Case.objects.create(organisation_name=ORGANISATION_NAME)
    form: MockForm = MockForm(cleaned_data={"case_search": ORGANISATION_NAME})

    filtered_cases: List[Case] = list(filter_cases(form))  # type: ignore

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
    """Test that searching for cases is reflected in the queryset"""
    Case.objects.create(organisation_name=ORGANISATION_NAME)
    Case.objects.create(
        organisation_name=ORGANISATION_NAME_COMPLAINT, is_complaint="yes"
    )
    form: MockForm = MockForm(cleaned_data={"is_complaint": is_complaint_filter})

    filtered_cases: List[Case] = list(filter_cases(form))  # type: ignore

    assert len(filtered_cases) == expected_number
    assert filtered_cases[0].organisation_name == expected_name


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
        (
            ColumnAndFieldNames(column_name="Contact notes", field_name=None),
            "notes1\n\nnotes2",
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
def test_download_equality_body_cases():
    """Test creation of CSV for equality bodies"""
    cases: List[Case] = [
        Case.objects.create(),
    ]
    response: HttpResponse = download_equality_body_cases(cases=cases, filename=CSV_EXPORT_FILENAME)  # type: ignore

    assert response.status_code == 200

    assert response.headers == {  # type: ignore
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    assert csv_header == [
        "Equality body",
        "Test type",
        "Case No.",
        "Case completed date",
        "Organisation",
        "Website URL",
        "Is it a complaint?",
        "Link to report",
        "Enforcement recommendation",
        "Enforcement recommendation notes",
        "Summary of progress made / response from PSB",
        "Disproportionate Burden Claimed?",
        "Disproportionate Burden Notes",
        "Accessibility Statement Decision",
        "Notes on accessibility statement",
        "Contact detail",
        "Contact name",
        "Job title",
        "Report sent on",
        "Report acknowledged",
        "Followup date - 12-week deadline",
        "Retest date",
        "Published report",
        "Initial disproportionate burden claimed?",
        "Initial disproportionate notes",
        "Final disproportionate burden claimed?",
        "Final disproportionate notes",
    ]
    assert csv_body == [
        [
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
            "",
            "",
            "",
        ]
    ]


@pytest.mark.django_db
def test_download_cases():
    """Test creation of CSV download of cases"""
    case: Case = Case.objects.create()
    cases: List[Case] = [case]
    Contact.objects.create(
        case=case, email="test@example.com", notes="Contact for CSV export"
    )

    response: HttpResponse = download_cases(cases=cases, filename=CSV_EXPORT_FILENAME)  # type: ignore

    assert response.status_code == 200

    assert response.headers == {  # type: ignore
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    assert csv_header == [
        "Case no.",
        "Version",
        "Created by",
        "Date created",
        "Status",
        "Auditor",
        "Type of test",
        "Full URL",
        "Domain name",
        "Organisation name",
        "Public sector body location",
        "Sector",
        "Which equalities body will check the case?",
        "Testing methodology",
        "Report methodology",
        "Complaint?",
        "URL to previous case",
        "Trello ticket URL",
        "Case details notes",
        "Case details page complete",
        "Link to test results spreadsheet",
        "Spreadsheet test status",
        "Initial accessibility statement compliance decision",
        "Initial accessibility statement compliance notes",
        "Initial website compliance decision",
        "Initial website compliance notes",
        "Testing details page complete",
        "Link to report draft",
        "Report details notes",
        "Report details page complete",
        "Report ready to be reviewed?",
        "QA auditor",
        "Report approved?",
        "QA notes",
        "Link to final PDF report",
        "Link to final ODT report",
        "QA process page complete",
        "Contact details page complete",
        "Report sent on",
        "1-week followup sent date",
        "4-week followup sent date",
        "Report acknowledged",
        "Zendesk ticket URL",
        "Report correspondence notes",
        "Report correspondence page complete",
        "1-week followup due date",
        "4-week followup due date",
        "12-week followup due date",
        "Do you want to mark the PSB as unresponsive to this case?",
        "12-week update requested",
        "12-week chaser 1-week followup sent date",
        "12-week update received",
        "12-week correspondence notes",
        "Mark the case as having no response to 12 week deadline",
        "12-week correspondence page complete",
        "12-week chaser 1-week followup due date",
        "12-week retest page complete",
        "Summary of progress made from public sector body",
        "Retested website?",
        "Is this case ready for final decision?",
        "Reviewing changes page complete",
        "12-week website compliance decision",
        "12-week website compliance decision notes",
        "Final website compliance decision page complete (spreadsheet testing)",
        "Disproportionate burden claimed? (spreadsheet testing)",
        "Disproportionate burden notes (spreadsheet testing)",
        "Link to accessibility statement screenshot (spreadsheet testing)",
        "12-week accessibility statement compliance decision",
        "12-week accessibility statement compliance notes",
        "Final accessibility statement compliance decision page complete (spreadsheet testing)",
        "Recommendation for equality body",
        "Enforcement recommendation notes",
        "Date when compliance decision email sent to public sector body",
        "Case completed",
        "Date case completed first updated",
        "Closing the case page complete",
        "Public sector body statement appeal notes",
        "Summary of events after the case was closed",
        "Post case summary page complete",
        "Case updated (on post case summary page)",
        "Date sent to equality body",
        "Equality body pursuing this case?",
        "Equality body correspondence notes",
        "Equality body summary page complete",
        "Deactivated case",
        "Date deactivated",
        "Reason why (deactivated)",
        "QA status",
        "Contact email",
        "Contact notes",
    ]
    assert csv_body == [
        [
            "1",
            "1",
            "",
            "14/12/2022",
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
            "Platform (requires Platform in testing methodology)",
            "No",
            "",
            "",
            "",
            "",
            "",
            "Not started",
            "Not selected",
            "",
            "Not selected",
            "",
            "",
            "",
            "",
            "",
            "Not started",
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
            "test@example.com",
            "Contact for CSV export",
        ]
    ]
