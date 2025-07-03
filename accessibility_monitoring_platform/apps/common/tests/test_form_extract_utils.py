"""
Test - common utility function to extract labels and values from forms
"""

from datetime import date

from django import forms
from django.contrib.auth.models import User

from ...cases.models import BaseCase
from ...simplified.models import SimplifiedCase
from ..form_extract_utils import FieldLabelAndValue, extract_form_labels_and_values
from ..forms import (
    AMPAuditorModelChoiceField,
    AMPChoiceRadioField,
    AMPDateField,
    AMPModelChoiceField,
    AMPTextField,
    AMPURLField,
)
from ..models import Sector

AUDITOR_LABEL: str = "Auditor"
SECTOR_LABEL: str = "Sector"
TEST_TYPE_LABEL: str = "Test type"
HOME_PAGE_URL_LABEL: str = "Full URL"
NOTES_LABEL: str = "Notes"
REPORT_SENT_ON_LABEL: str = "Report sent on"


class CaseForm(forms.ModelForm):
    """
    Form for testing extract_labels_and_values
    """

    auditor = AMPAuditorModelChoiceField(label=AUDITOR_LABEL)
    sector = AMPModelChoiceField(label=SECTOR_LABEL, queryset=Sector.objects.all())
    test_type = AMPChoiceRadioField(
        label=TEST_TYPE_LABEL, choices=BaseCase.TestType.choices
    )
    home_page_url = AMPURLField(
        label=HOME_PAGE_URL_LABEL,
        help_text="Enter if test type is simplified or detailed",
        required=True,
    )
    notes = AMPTextField(label=NOTES_LABEL)
    report_sent_date = AMPDateField(label=REPORT_SENT_ON_LABEL)

    class Meta:
        model = BaseCase
        fields = [
            "auditor",
            "sector",
            "test_type",
            "home_page_url",
            "notes",
            "report_sent_date",
        ]


def test_extract_form_labels_and_values():
    """
    Test extraction of labels from form and values from case.
    """
    auditor: User = User(first_name="first", last_name="second")
    sector: Sector = Sector(name="sector name")
    simplified_case: SimplifiedCase = SimplifiedCase(
        auditor=auditor,
        sector=sector,
        test_type="simplified",
        home_page_url="https://home-page-url.com",
        notes="notes",
        report_sent_date=date(2020, 4, 1),
    )

    labels_and_values: list[FieldLabelAndValue] = extract_form_labels_and_values(
        instance=simplified_case, form=CaseForm()
    )

    assert len(labels_and_values) == 6
    assert labels_and_values[0] == FieldLabelAndValue(
        label=AUDITOR_LABEL, value=auditor.get_full_name()
    )
    assert labels_and_values[1] == FieldLabelAndValue(
        label=SECTOR_LABEL, value=sector.name
    )
    assert labels_and_values[2] == FieldLabelAndValue(
        label=TEST_TYPE_LABEL, value=simplified_case.get_test_type_display()
    )
    assert labels_and_values[3] == FieldLabelAndValue(
        label=HOME_PAGE_URL_LABEL,
        value=simplified_case.home_page_url,
        type=FieldLabelAndValue.Type.URL,
    )
    assert labels_and_values[4] == FieldLabelAndValue(
        label=NOTES_LABEL,
        value=simplified_case.notes,
        type=FieldLabelAndValue.Type.NOTES,
    )
    assert labels_and_values[5] == FieldLabelAndValue(
        label=REPORT_SENT_ON_LABEL,
        value=simplified_case.report_sent_date,
        type=FieldLabelAndValue.Type.DATE,
    )


def test_extract_form_labels_and_values_with_no_values_set():
    """
    Test extraction of labels from form and values from case when
    there are no values populated.
    """
    simplified_case: SimplifiedCase = SimplifiedCase()

    labels_and_values: list[FieldLabelAndValue] = extract_form_labels_and_values(
        instance=simplified_case, form=CaseForm()
    )

    assert len(labels_and_values) == 5
    assert labels_and_values[0] == FieldLabelAndValue(label=AUDITOR_LABEL, value=None)
    assert labels_and_values[1] == FieldLabelAndValue(
        label=SECTOR_LABEL, value="Unknown"
    )
    assert labels_and_values[2] == FieldLabelAndValue(
        label=TEST_TYPE_LABEL, value=simplified_case.get_test_type_display()
    )
    assert labels_and_values[3] == FieldLabelAndValue(
        label=HOME_PAGE_URL_LABEL,
        value="",
        type=FieldLabelAndValue.Type.URL,
    )
    assert labels_and_values[4] == FieldLabelAndValue(
        label=REPORT_SENT_ON_LABEL,
        value=None,
    )


def test_extract_form_labels_and_values_can_exclude_fields():
    """
    Test fields can be excluded from extraction of labels from form and values
    from case.
    """
    simplified_case: SimplifiedCase = SimplifiedCase()

    labels_and_values: list[FieldLabelAndValue] = extract_form_labels_and_values(
        instance=simplified_case,
        form=CaseForm(),
        excluded_fields=["home_page_url", "report_sent_date"],
    )

    assert len(labels_and_values) == 3
    assert labels_and_values[0] == FieldLabelAndValue(label=AUDITOR_LABEL, value=None)
    assert labels_and_values[1] == FieldLabelAndValue(
        label=SECTOR_LABEL, value="Unknown"
    )
    assert labels_and_values[2] == FieldLabelAndValue(
        label=TEST_TYPE_LABEL, value=simplified_case.get_test_type_display()
    )
