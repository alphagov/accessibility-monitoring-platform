"""
Test utility functions of cases app
"""

import csv
import io
from datetime import date, datetime, timezone
from typing import Any, Generator

import pytest
from django.contrib.auth.models import User
from django.http import HttpResponse, StreamingHttpResponse

from ...audits.models import Audit
from ...cases.csv_export import (
    csv_output_generator,
    populate_csv_columns,
    populate_equality_body_columns,
)
from ...common.csv_export import CSVColumn, EqualityBodyCSVColumn, format_model_field
from ...detailed.csv_export import DETAILED_CASE_COLUMNS_FOR_EXPORT
from ...detailed.models import Contact as DetailedContact
from ...detailed.models import DetailedCase
from ...simplified.csv_export import (
    SIMPLIFIED_CASE_COLUMNS_FOR_EXPORT,
    SIMPLIFIED_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
    SIMPLIFIED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
    format_simplified_contacts,
)
from ...simplified.models import CaseCompliance
from ...simplified.models import Contact as SimplifiedContact
from ...simplified.models import SimplifiedCase
from ..csv_export_utils import (
    download_detailed_cases,
    download_equality_body_cases,
    download_simplified_cases,
    download_simplified_feedback_survey_cases,
)

CONTACTS: list[SimplifiedContact] = [
    SimplifiedContact(
        name="Name 1",
        job_title="Job title 1",
        email="email1",
    ),
    SimplifiedContact(
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
SIMPLIFIED_CONTACT_NOTES: str = "Simplified contact notes"
SIMPLIFIED_CONTACT_EMAIL: str = "simplified@example.com"
DETAILED_CONTACT_NAME: str = "Detailed contact name"
DETAILED_CONTACT_TITLE: str = "Detailed contact job title"
DETAILED_CONTACT_DETAILS: str = "Detailed contact details"


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

    assert len(first_data_row) == len(expected_first_data_row)

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
    assert format_simplified_contacts(contacts=CONTACTS) == EXPECTED_FORMATTED_CONTACTS


@pytest.mark.django_db
def test_download_feedback_survey_cases():
    """Test creation of CSV for feedback survey"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        compliance_email_sent_date=datetime(2022, 12, 16, tzinfo=timezone.utc),
        contact_notes=SIMPLIFIED_CONTACT_NOTES,
    )
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_cases: list[SimplifiedCase] = [simplified_case]

    response: HttpResponse = download_simplified_feedback_survey_cases(
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
        "",  # Organisation name
        "16/12/2022",  # Closing the case date
        "Not selected",  # Enforcement recommendation
        "",  # Enforcement recommendation notes
        "Not assessed",  # statement_compliance_state_12_week
        "",  # Contact email
        SIMPLIFIED_CONTACT_NOTES,  # Contact notes
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
        column.column_header for column in SIMPLIFIED_EQUALITY_BODY_COLUMNS_FOR_EXPORT
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
    SimplifiedContact.objects.create(
        simplified_case=simplified_case, email="test@example.com"
    )

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
def test_download_cases_detailed():
    """Test creation of CSV download of detailed cases"""
    user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    detailed_case: DetailedCase = DetailedCase.objects.create()
    detailed_case.created = datetime(2022, 12, 16, tzinfo=timezone.utc)
    detailed_case.save()
    detailed_cases: list[DetailedCase] = [detailed_case]
    DetailedContact.objects.create(
        detailed_case=detailed_case,
        name=DETAILED_CONTACT_NAME,
        job_title=DETAILED_CONTACT_TITLE,
        contact_details=DETAILED_CONTACT_DETAILS,
        created_by=user,
    )

    response: HttpResponse = download_detailed_cases(
        detailed_cases=detailed_cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: list[str] = [
        column.column_header for column in DETAILED_CASE_COLUMNS_FOR_EXPORT
    ]

    expected_first_data_row: list[str] = [
        "1",
        "2",
        "",
        "16/12/2022",
        "Unassigned case",
        "",
        "Detailed",
        "",
        "",
        "",
        "",
        "",
        "",
        "EHRC",
        "Website",
        "Unknown",
        "",
        "No",
        "",
        "No",
        "",
        DETAILED_CONTACT_NAME,
        DETAILED_CONTACT_TITLE,
        DETAILED_CONTACT_DETAILS,
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "Not known",
        "Not assessed",
        "Not checked",
        "",
        "No",
        "",
        "",
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
        "",
        "Not known",
        "",
        "Not assessed",
        "",
        "Not checked",
        "",
        "",
        "",
        "Not selected",
        "",
        "",
        "",
        "Case still in progress",
        "No",
        "",
        "",
        "",
        "",
        "",
        "",
        "No (or holding)",
        "",
        "",
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
def test_populate_equality_body_columns():
    """Test collection of case data for equality body export"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    SimplifiedContact.objects.create(
        simplified_case=simplified_case, email=SIMPLIFIED_CONTACT_EMAIL
    )
    row: list[CSVColumn] = populate_equality_body_columns(case=simplified_case)

    assert len(row) == 30

    contact_details: list[EqualityBodyCSVColumn] = [
        cell for cell in row if cell.column_header == "Contact details"
    ]

    assert len(contact_details) == 1

    contact_details_cell: EqualityBodyCSVColumn = contact_details[0]

    assert contact_details_cell.formatted_data == f"{SIMPLIFIED_CONTACT_EMAIL}\n"
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
def test_populate_csv_columns_simplified():
    """Test collection of case data for CSV export for simplified case"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_case.update_case_status()
    SimplifiedContact.objects.create(
        simplified_case=simplified_case, email=SIMPLIFIED_CONTACT_EMAIL
    )
    row: list[CSVColumn] = populate_csv_columns(
        case=simplified_case,
        column_definitions=SIMPLIFIED_CASE_COLUMNS_FOR_EXPORT,
    )

    assert len(row) == 92

    contact_email: list[CSVColumn] = [
        cell for cell in row if cell.column_header == "Contact email"
    ]

    assert len(contact_email) == 1

    contact_email_cell: CSVColumn = contact_email[0]

    assert contact_email_cell.formatted_data == SIMPLIFIED_CONTACT_EMAIL


@pytest.mark.django_db
def test_populate_csv_columns_detailed():
    """Test collection of case data for CSV export for detailed case"""
    detailed_case: DetailedCase = DetailedCase.objects.create()
    row: list[CSVColumn] = populate_csv_columns(
        case=detailed_case,
        column_definitions=DETAILED_CASE_COLUMNS_FOR_EXPORT,
    )

    assert len(row) == 83

    # contact_email: list[CSVColumn] = [
    #     cell for cell in row if cell.column_header == "Contact email"
    # ]

    # assert len(contact_email) == 1

    # contact_email_cell: CSVColumn = contact_email[0]

    # assert contact_email_cell.formatted_data == CONTACT_EMAIL


@pytest.mark.django_db
def test_populate_feedback_survey_columns():
    """Test collection of case data for feedback survey export"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_case.update_case_status()
    SimplifiedContact.objects.create(
        simplified_case=simplified_case, email=SIMPLIFIED_CONTACT_EMAIL
    )
    row: list[CSVColumn] = populate_csv_columns(
        case=simplified_case,
        column_definitions=SIMPLIFIED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
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
        cases=simplified_cases, columns_for_export=SIMPLIFIED_CASE_COLUMNS_FOR_EXPORT
    )

    first_yield: str = next(generator)

    assert first_yield.count("\n") == 2

    second_yield: str = next(generator)

    assert second_yield.count("\n") == 500

    with pytest.raises(StopIteration):
        next(generator)
