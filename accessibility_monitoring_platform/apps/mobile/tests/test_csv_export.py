"""Test utility functions of mobile CSV export"""

from typing import Generator

import pytest
from django.contrib.auth.models import User

from ...cases.csv_export import populate_csv_columns
from ...common.csv_export import CSVColumn, EqualityBodyCSVColumn
from ..csv_export import (
    MOBILE_CASE_COLUMNS_FOR_EXPORT,
    MOBILE_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
    MOBILE_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
    MobileEqualityBodyCSVColumn,
    csv_mobile_equality_body_output_generator,
    populate_mobile_equality_body_columns,
)
from ..models import MobileCase, MobileContact

MOBILE_CONTACT_NAME: str = "Mobile contact name"
MOBILE_CONTACT_TITLE: str = "Mobile contact job title"
MOBILE_CONTACT_DETAILS: str = "name@domain.com"
IOS_NUMBER_OF_ISSUES: int = 3
ANDROID_NUMBER_OF_ISSUES: int = 7
TOTAL_NUMBER_OF_ISSUES: int = 10


@pytest.mark.django_db
def test_populate_csv_columns():
    """Test collection of case data for CSV export for mobile case"""
    mobile_case: MobileCase = MobileCase.objects.create()
    user: User = User.objects.create()
    MobileContact.objects.create(
        mobile_case=mobile_case,
        created_by=user,
        name=MOBILE_CONTACT_NAME,
        job_title=MOBILE_CONTACT_TITLE,
        contact_details=MOBILE_CONTACT_DETAILS,
    )
    row: list[CSVColumn] = populate_csv_columns(
        case=mobile_case,
        column_definitions=MOBILE_CASE_COLUMNS_FOR_EXPORT,
    )

    assert len(row) == 95

    contact_name: list[CSVColumn] = [
        cell for cell in row if cell.column_header == "Contact name"
    ]

    assert len(contact_name) == 1

    contact_name_cell: CSVColumn = contact_name[0]

    assert contact_name_cell.formatted_data == MOBILE_CONTACT_NAME


@pytest.mark.django_db
def test_populate_feedback_survey_columns_mobile():
    """Test collection of case data for feedback survey export for mobile case"""
    mobile_case: MobileCase = MobileCase.objects.create()
    user: User = User.objects.create()
    MobileContact.objects.create(
        mobile_case=mobile_case,
        created_by=user,
        name=MOBILE_CONTACT_NAME,
        job_title=MOBILE_CONTACT_TITLE,
        contact_details=MOBILE_CONTACT_DETAILS,
    )
    row: list[CSVColumn] = populate_csv_columns(
        case=mobile_case,
        column_definitions=MOBILE_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
    )

    assert len(row) == 10


@pytest.mark.django_db
def test_populate_mobile_equality_body_columns():
    """Test collection of case data for equality body export for mobile case"""
    mobile_case: MobileCase = MobileCase.objects.create()
    user: User = User.objects.create()
    MobileContact.objects.create(
        mobile_case=mobile_case,
        created_by=user,
        name=MOBILE_CONTACT_NAME,
        job_title=MOBILE_CONTACT_TITLE,
        contact_details=MOBILE_CONTACT_DETAILS,
    )
    row: list[EqualityBodyCSVColumn | MobileEqualityBodyCSVColumn] = (
        populate_mobile_equality_body_columns(mobile_case=mobile_case)
    )

    assert len(row) == 29

    contact_details: list[EqualityBodyCSVColumn] = [
        cell for cell in row if cell.column_header == "Contact details"
    ]

    assert len(contact_details) == 1

    contact_details_cell: EqualityBodyCSVColumn = contact_details[0]

    assert (
        contact_details_cell.formatted_data
        == f"{MOBILE_CONTACT_NAME}\n{MOBILE_CONTACT_TITLE}\n{MOBILE_CONTACT_DETAILS}\n"
    )
    assert contact_details_cell.edit_url_name == "mobile:manage-contact-details"
    assert contact_details_cell.edit_url == "/mobile/1/manage-contact-details/"

    organisation_responded: list[EqualityBodyCSVColumn] = [
        cell
        for cell in row
        if cell.column_header == "Organisation responded to report?"
    ]

    assert len(organisation_responded) == 1

    organisation_responded_cell: EqualityBodyCSVColumn = organisation_responded[0]

    assert organisation_responded_cell.formatted_data == "No"
    assert (
        organisation_responded_cell.edit_url_name == "mobile:edit-report-acknowledged"
    )
    assert (
        organisation_responded_cell.edit_url
        == "/mobile/1/edit-report-acknowledged/#id_report_acknowledged_date-label"
    )


@pytest.mark.django_db
def test_populate_mobile_equality_body_columns_separate_os():
    """
    Test collection of case data for equality body export for mobile case where
    iOS and Android data is shown separately
    """
    mobile_case: MobileCase = MobileCase.objects.create()
    row: list[EqualityBodyCSVColumn | MobileEqualityBodyCSVColumn] = (
        populate_mobile_equality_body_columns(mobile_case=mobile_case)
    )

    published_report: list[MobileEqualityBodyCSVColumn] = [
        cell for cell in row if cell.column_header == "Published report"
    ]

    assert len(published_report) == 1

    published_report_cell: MobileEqualityBodyCSVColumn = published_report[0]

    assert published_report_cell.formatted_data == "iOS: n/a\n\nAndroid: n/a"
    assert published_report_cell.ios_edit_url_name == "mobile:edit-final-report"
    assert (
        published_report_cell.ios_edit_url
        == "/mobile/1/edit-final-report/#id_equality_body_report_url_ios-label"
    )
    assert published_report_cell.android_edit_url_name == "mobile:edit-final-report"
    assert (
        published_report_cell.android_edit_url
        == "/mobile/1/edit-final-report/#id_equality_body_report_url_android-label"
    )


@pytest.mark.django_db
def test_populate_mobile_equality_body_columns_combined_os():
    """
    Test collection of case data for equality body export for mobile case where
    iOS and Android data is combined
    """
    mobile_case: MobileCase = MobileCase.objects.create(
        initial_ios_total_number_of_issues=IOS_NUMBER_OF_ISSUES,
        initial_android_total_number_of_issues=ANDROID_NUMBER_OF_ISSUES,
    )
    row: list[EqualityBodyCSVColumn | MobileEqualityBodyCSVColumn] = (
        populate_mobile_equality_body_columns(mobile_case=mobile_case)
    )

    total_number_of_issues_column: list[
        EqualityBodyCSVColumn | MobileEqualityBodyCSVColumn
    ] = [
        cell
        for cell in row
        if cell.column_header == "Total number of accessibility issues"
    ]

    assert len(total_number_of_issues_column) == 1

    total_number_of_issues_cell: EqualityBodyCSVColumn | MobileEqualityBodyCSVColumn = (
        total_number_of_issues_column[0]
    )

    assert total_number_of_issues_cell.formatted_data == TOTAL_NUMBER_OF_ISSUES
    assert (
        total_number_of_issues_cell.ios_edit_url_name
        == "mobile:edit-initial-test-ios-outcome"
    )
    assert (
        total_number_of_issues_cell.ios_edit_url
        == "/mobile/1/edit-initial-test-ios-outcome/#id_initial_ios_total_number_of_issues-label"
    )
    assert (
        total_number_of_issues_cell.android_edit_url_name
        == "mobile:edit-initial-test-android-outcome"
    )
    assert (
        total_number_of_issues_cell.android_edit_url
        == "/mobile/1/edit-initial-test-android-outcome/#id_initial_android_total_number_of_issues-label"
    )


@pytest.mark.django_db
def test_csv_mobile_equality_body_output_generator():
    """
    Test CSV output generator returns:

    1. Column headers and first Case
    2. Next 500 Cases (current DOWNLOAD_CASES_CHUNK_SIZE)
    3. Stops after all Cases returned
    """
    mobile_case: MobileCase = MobileCase.objects.create()
    mobile_cases: list[MobileCase] = [mobile_case for _ in range(501)]

    generator: Generator[str, None, None] = csv_mobile_equality_body_output_generator(
        mobile_cases=mobile_cases
    )

    first_yield: str = next(generator)

    assert first_yield.startswith(
        ",".join(
            [column.column_header for column in MOBILE_EQUALITY_BODY_COLUMNS_FOR_EXPORT]
        )
    )

    second_yield: str = next(generator)

    assert len(second_yield) > 100_000  # The bulk of the mobile case data

    with pytest.raises(StopIteration):
        next(generator)
