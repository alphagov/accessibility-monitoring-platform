"""Test utility functions of cases CSV export"""

from typing import Generator

import pytest

from ...common.csv_export import CSVColumn, EqualityBodyCSVColumn
from ...detailed.csv_export import DETAILED_CASE_COLUMNS_FOR_EXPORT
from ...detailed.models import DetailedCase
from ...simplified.csv_export import (
    SIMPLIFIED_CASE_COLUMNS_FOR_EXPORT,
    SIMPLIFIED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
)
from ...simplified.models import CaseCompliance
from ...simplified.models import Contact as SimplifiedContact
from ...simplified.models import SimplifiedCase
from ..csv_export import (
    csv_output_generator,
    populate_csv_columns,
    populate_equality_body_columns,
)

SIMPLIFIED_CONTACT_NOTES: str = "Simplified contact notes"
SIMPLIFIED_CONTACT_EMAIL: str = "simplified@example.com"
DETAILED_CONTACT_NAME: str = "Detailed contact name"
DETAILED_CONTACT_TITLE: str = "Detailed contact job title"
DETAILED_CONTACT_DETAILS: str = "Detailed contact details"


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

    assert len(row) == 83

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

    assert len(row) == 11


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


@pytest.mark.django_db
def test_populate_equality_body_columns():
    """Test collection of case data for equality body export"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    SimplifiedContact.objects.create(
        simplified_case=simplified_case, email=SIMPLIFIED_CONTACT_EMAIL
    )
    row: list[CSVColumn] = populate_equality_body_columns(case=simplified_case)

    assert len(row) == 29

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
