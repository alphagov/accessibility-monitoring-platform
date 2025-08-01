"""
Test utility functions of cases app
"""

import csv
import io
from datetime import date, datetime, timezone
from typing import Any, Generator

import pytest
from django.http import HttpResponse, StreamingHttpResponse

from ...audits.models import Audit
from ...simplified.models import CaseCompliance, Contact, SimplifiedCase
from ..csv_export_utils import (
    CASE_COLUMNS_FOR_EXPORT,
    EQUALITY_BODY_COLUMNS_FOR_EXPORT,
    FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
    CSVColumn,
    EqualityBodyCSVColumn,
    csv_output_generator,
    download_equality_body_cases,
    download_feedback_survey_cases,
    download_simplified_cases,
    format_contacts,
    format_model_field,
    populate_csv_columns,
    populate_equality_body_columns,
)

CONTACTS: list[Contact] = [
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
EXPECTED_FORMATTED_CONTACTS: str = """Name 1
Job title 1
email1

Name 2
Job title 2
email2
"""

CSV_EXPORT_FILENAME: str = "cases_export.csv"
CONTACT_NOTES: str = "Contact notes"
CONTACT_EMAIL: str = "example@example.com"


def decode_csv_response(
    response: StreamingHttpResponse,
) -> tuple[list[str], list[list[str]]]:
    """Decode CSV HTTP response and break into column names and data"""
    content_chunks: list[str] = [
        chunk.decode("utf-8") for chunk in response.streaming_content
    ]
    content: str = "".join(content_chunks)
    csv_reader: Any = csv.reader(io.StringIO(content))
    csv_body: list[list[str]] = list(csv_reader)
    csv_header: list[str] = csv_body.pop(0)
    return csv_header, csv_body


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


def test_format_case_field_with_no_data():
    """
    Test that format_model_field returns empty string if no model instance
    """
    assert (
        format_model_field(
            source_instance=None,
            column=CSVColumn(
                column_header="A", source_class=SimplifiedCase, source_attr="a"
            ),
        )
        == ""
    )


@pytest.mark.parametrize(
    "column, case_value, expected_formatted_value",
    [
        (
            CSVColumn(
                column_header="Test type",
                source_class=SimplifiedCase,
                source_attr="test_type",
            ),
            "simplified",
            "Simplified",
        ),
        (
            CSVColumn(
                column_header="Report sent on",
                source_class=SimplifiedCase,
                source_attr="report_sent_date",
            ),
            date(2020, 12, 31),
            "31/12/2020",
        ),
        (
            CSVColumn(
                column_header="Enforcement recommendation",
                source_class=SimplifiedCase,
                source_attr="recommendation_for_enforcement",
            ),
            "no-further-action",
            "No further action",
        ),
        (
            CSVColumn(
                column_header="Which equality body will check the case",
                source_class=SimplifiedCase,
                source_attr="enforcement_body",
            ),
            "ehrc",
            "EHRC",
        ),
    ],
)
def test_format_case_field(column, case_value, expected_formatted_value):
    """Test that case fields are formatted correctly"""
    simplified_case: SimplifiedCase = SimplifiedCase()
    setattr(simplified_case, column.source_attr, case_value)
    assert expected_formatted_value == format_model_field(
        source_instance=simplified_case, column=column
    )


def test_format_contacts():
    """Test that contacts fields values are contatenated"""
    assert format_contacts(contacts=CONTACTS) == EXPECTED_FORMATTED_CONTACTS


@pytest.mark.django_db
def test_download_feedback_survey_cases():
    """Test creation of CSV for feedback survey"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        compliance_email_sent_date=datetime(2022, 12, 16, tzinfo=timezone.utc),
        contact_notes=CONTACT_NOTES,
    )
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_cases: list[SimplifiedCase] = [simplified_case]

    response: HttpResponse = download_feedback_survey_cases(
        cases=simplified_cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: list[str] = [
        column.column_header for column in FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT
    ]
    expected_first_data_row: list[str] = [
        "1",  # Case no.
        "",  # Organisation name
        "16/12/2022",  # Closing the case date
        "Not selected",  # Enforcement recommendation
        "",  # Enforcement recommendation notes
        "Not assessed",  # statement_compliance_state_12_week
        "",  # Contact email
        CONTACT_NOTES,  # Contact notes
        "No",  # Feedback survey sent
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
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_cases: list[SimplifiedCase] = [simplified_case]
    Audit.objects.create(simplified_case=simplified_case)

    response: HttpResponse = download_equality_body_cases(
        cases=simplified_cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: list[str] = [
        column.column_header for column in EQUALITY_BODY_COLUMNS_FOR_EXPORT
    ]

    expected_first_data_row: list[str] = [
        "EHRC",
        "Simplified",
        "1",
        "",
        "",
        "",
        "",
        "",
        "",
        "No",
        "",
        "Not selected",
        "",
        "",
        "",
        "No",
        "",
        "",
        "",
        "",
        "",
        "",
        "0",
        "0",
        "0",
        "n/a",
        "Yes",
        "Not assessed",
        "Not checked",
        "",
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
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        contact_notes="Contact for CSV export",
    )
    simplified_case.created = datetime(2022, 12, 16, tzinfo=timezone.utc)
    simplified_case.save()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_case.update_case_status()
    simplified_cases: list[SimplifiedCase] = [simplified_case]
    Contact.objects.create(simplified_case=simplified_case, email="test@example.com")

    response: HttpResponse = download_simplified_cases(
        simplified_cases=simplified_cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: list[str] = [
        column.column_header for column in CASE_COLUMNS_FOR_EXPORT
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
def test_populate_equality_body_columns():
    """Test collection of case data for equality body export"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    Contact.objects.create(simplified_case=simplified_case, email=CONTACT_EMAIL)
    row: list[CSVColumn] = populate_equality_body_columns(
        simplified_case=simplified_case
    )

    assert len(row) == 30

    contact_details: list[EqualityBodyCSVColumn] = [
        cell for cell in row if cell.column_header == "Contact details"
    ]

    assert len(contact_details) == 1

    contact_details_cell: EqualityBodyCSVColumn = contact_details[0]

    assert contact_details_cell.formatted_data == f"{CONTACT_EMAIL}\n"
    assert contact_details_cell.edit_url_name == "simplified:manage-contact-details"
    assert contact_details_cell.edit_url == "/simplified/1/manage-contact-details/"

    organisation_responded: list[EqualityBodyCSVColumn] = [
        cell
        for cell in row
        if cell.column_header == "Organisation responded to report?"
    ]

    assert len(organisation_responded) == 1

    organisation_responded_cell: EqualityBodyCSVColumn = organisation_responded[0]

    assert organisation_responded_cell.formatted_data == "No"
    assert (
        organisation_responded_cell.edit_url_name
        == "simplified:edit-report-acknowledged"
    )
    assert (
        organisation_responded_cell.edit_url
        == "/simplified/1/edit-report-acknowledged/#id_report_acknowledged_date-label"
    )


@pytest.mark.django_db
def test_populate_csv_columns():
    """Test collection of case data for CSV export"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_case.update_case_status()
    Contact.objects.create(simplified_case=simplified_case, email=CONTACT_EMAIL)
    row: list[CSVColumn] = populate_csv_columns(
        simplified_case=simplified_case, column_definitions=CASE_COLUMNS_FOR_EXPORT
    )

    assert len(row) == 92

    contact_email: list[CSVColumn] = [
        cell for cell in row if cell.column_header == "Contact email"
    ]

    assert len(contact_email) == 1

    contact_email_cell: CSVColumn = contact_email[0]

    assert contact_email_cell.formatted_data == CONTACT_EMAIL


@pytest.mark.django_db
def test_populate_feedback_survey_columns():
    """Test collection of case data for feedback survey export"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_case.update_case_status()
    Contact.objects.create(simplified_case=simplified_case, email=CONTACT_EMAIL)
    row: list[CSVColumn] = populate_csv_columns(
        simplified_case=simplified_case,
        column_definitions=FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
    )

    assert len(row) == 9


@pytest.mark.django_db
def test_csv_output_generator():
    """
    Test CSV output generator returns:

    1. Column headers and first Case
    2. Next 500 Cases (current DOWNLOAD_CASES_CHUNK_SIZE)
    3. Stops after all Cases returned
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_cases: list[SimplifiedCase] = [simplified_case for _ in range(501)]

    generator: Generator[str, None, None] = csv_output_generator(
        cases=simplified_cases, columns_for_export=CASE_COLUMNS_FOR_EXPORT
    )

    first_yield: str = next(generator)

    assert first_yield.count("\n") == 2

    second_yield: str = next(generator)

    assert second_yield.count("\n") == 500

    with pytest.raises(StopIteration):
        next(generator)
