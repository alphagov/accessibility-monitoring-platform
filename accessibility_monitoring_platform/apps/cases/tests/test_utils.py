"""
Test utility functions of cases app
"""
import pytest

from dataclasses import dataclass
from datetime import date
from typing import Dict, List


from ..models import Case, Contact
from ..utils import (
    get_sent_date,
    filter_cases,
    ColumnAndFieldNames,
    format_case_field,
    format_contacts,
)

ORGANISATION_NAME: str = "Organisation name one"

CONTACTS = [
    Contact(
        first_name="First 1",
        last_name="Last 1",
        job_title="Job title 1",
        email="email1",
        notes="notes1",
    ),
    Contact(
        first_name="First 2",
        last_name="Last 2",
        job_title="Job title 2",
        email="email2",
        notes="notes2",
    ),
]


@dataclass
class MockCase:
    """Mock of case for testing"""

    sent_date: str


@dataclass
class MockForm:
    """Mock of form for testing"""

    cleaned_data: Dict[str, str]


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
    form: MockForm = MockForm(cleaned_data={"search": ORGANISATION_NAME})

    filtered_cases: List[Case] = list(filter_cases(form))  # type: ignore

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == ORGANISATION_NAME


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
            "no-action",
            "No action",
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
    assert expected_formatted_value == format_case_field(case=case, column=column)


@pytest.mark.parametrize(
    "column, expected_formatted_value",
    [
        (
            ColumnAndFieldNames(column_name="Contact name", field_name=None),
            "First 1 Last 1\nFirst 2 Last 2",
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
