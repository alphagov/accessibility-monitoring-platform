"""
Test utility functions of cases app
"""
import pytest

from dataclasses import dataclass
from datetime import date
from typing import Dict, List

from django import forms
from django.contrib.auth.models import User

from ...common.models import Sector
from ...common.forms import (
    AMPChoiceRadioField,
    AMPDateField,
    AMPModelChoiceField,
    AMPTextField,
    AMPURLField,
    AMPUserModelChoiceField,
)
from ..models import Case, TEST_TYPE_CHOICES
from ..utils import CaseFieldLabelAndValue, extract_labels_and_values, get_sent_date

AUDITOR_LABEL = "Auditor"
SECTOR_LABEL = "Sector"
TEST_TYPE_LABEL = "Test type"
HOME_PAGE_URL_LABEL = "Full URL"
NOTES_LABEL = "Notes"
REPORT_SENT_ON_LABEL = "Report sent on"


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
        get_sent_date(
            form=mock_form, case_from_db=mock_case, sent_date_name="sent_date"
        )
        == expected_date
    )


class CaseForm(forms.ModelForm):
    """
    Form for testing extract_labels_and_values
    """

    auditor = AMPUserModelChoiceField(label=AUDITOR_LABEL)
    sector = AMPModelChoiceField(label=SECTOR_LABEL, queryset=Sector.objects.all())
    test_type = AMPChoiceRadioField(label=TEST_TYPE_LABEL, choices=TEST_TYPE_CHOICES)
    home_page_url = AMPURLField(
        label=HOME_PAGE_URL_LABEL,
        help_text="Enter if test type is simplified or detailed",
        required=True,
    )
    notes = AMPTextField(label=NOTES_LABEL)
    report_sent_date = AMPDateField(label=REPORT_SENT_ON_LABEL)

    class Meta:
        model = Case
        fields = [
            "auditor",
            "sector",
            "test_type",
            "home_page_url",
            "notes",
            "report_sent_date",
        ]


def test_extract_labels_and_values():
    """
    Test extraction of labels from form and values from case.
    """
    auditor: User = User(first_name="first", last_name="second")
    sector: Sector = Sector(name="sector name")
    case: Case = Case(
        auditor=auditor,
        sector=sector,
        test_type="simplified",
        home_page_url="https://home-page-url.com",
        notes="notes",
        report_sent_date=date(2020, 4, 1),
    )

    labels_and_values: List[CaseFieldLabelAndValue] = extract_labels_and_values(
        case=case, form=CaseForm()
    )

    assert len(labels_and_values) == 6
    assert labels_and_values[0] == CaseFieldLabelAndValue(
        label=AUDITOR_LABEL, value=auditor.get_full_name()
    )
    assert labels_and_values[1] == CaseFieldLabelAndValue(
        label=SECTOR_LABEL, value=sector
    )
    assert labels_and_values[2] == CaseFieldLabelAndValue(
        label=TEST_TYPE_LABEL, value=case.get_test_type_display()
    )
    assert labels_and_values[3] == CaseFieldLabelAndValue(
        label=HOME_PAGE_URL_LABEL,
        value=case.home_page_url,
        type=CaseFieldLabelAndValue.URL_TYPE,
    )
    assert labels_and_values[4] == CaseFieldLabelAndValue(
        label=NOTES_LABEL, value=case.notes, type=CaseFieldLabelAndValue.NOTES_TYPE
    )
    assert labels_and_values[5] == CaseFieldLabelAndValue(
        label=REPORT_SENT_ON_LABEL,
        value=case.report_sent_date,
        type=CaseFieldLabelAndValue.DATE_TYPE,
    )


def test_extract_labels_and_values_with_no_values_set():
    """
    Test extraction of labels from form and values from case when there are no values populated.
    """
    case: Case = Case()

    labels_and_values: List[CaseFieldLabelAndValue] = extract_labels_and_values(
        case=case, form=CaseForm()
    )

    assert len(labels_and_values) == 6
    assert labels_and_values[0] == CaseFieldLabelAndValue(
        label=AUDITOR_LABEL, value=None
    )
    assert labels_and_values[1] == CaseFieldLabelAndValue(
        label=SECTOR_LABEL, value="Unknown"
    )
    assert labels_and_values[2] == CaseFieldLabelAndValue(
        label=TEST_TYPE_LABEL, value=case.get_test_type_display()
    )
    assert labels_and_values[3] == CaseFieldLabelAndValue(
        label=HOME_PAGE_URL_LABEL,
        value="",
        type=CaseFieldLabelAndValue.URL_TYPE,
    )
    assert labels_and_values[4] == CaseFieldLabelAndValue(
        label=NOTES_LABEL, value="", type=CaseFieldLabelAndValue.NOTES_TYPE
    )
    assert labels_and_values[5] == CaseFieldLabelAndValue(
        label=REPORT_SENT_ON_LABEL,
        value=None,
    )
