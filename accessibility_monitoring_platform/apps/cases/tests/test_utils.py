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

from ...audits.models import Audit
from ..models import Case, Contact
from ..utils import (
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
    case: Case = Case.objects.create()
    cases: List[Case] = [case]
    Audit.objects.create(
        case=case, audit_retest_disproportionate_burden_notes="Audit for CSV export"
    )

    response: HttpResponse = download_equality_body_cases(cases=cases, filename=CSV_EXPORT_FILENAME)  # type: ignore

    assert response.status_code == 200

    assert response.headers == {  # type: ignore
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    assert csv_header == [
        column.column_name
        for column in COLUMNS_FOR_EQUALITY_BODY + EXTRA_AUDIT_COLUMNS_FOR_EQUALITY_BODY
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
            "No claim",
            "",
            "No claim",
            "Audit for CSV export",
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
        column.column_name
        for column in CASE_COLUMNS_FOR_EXPORT + CONTACT_COLUMNS_FOR_EXPORT
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
