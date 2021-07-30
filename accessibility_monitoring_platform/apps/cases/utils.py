"""
Utility functions for cases app
"""

from dataclasses import dataclass
from datetime import date
from typing import ClassVar, List, Union

from django import forms
from django.contrib.auth.models import User

from ..common.forms import AMPDateField, AMPTextField, AMPURLField

from .forms import (
    CaseDetailUpdateForm,
    CaseTestResultsUpdateForm,
    CaseReportDetailsUpdateForm,
    CaseReportCorrespondenceUpdateForm,
    CaseFinalDecisionUpdateForm,
)

from .models import Case

EXTRA_LABELS = {
    "test_results_url": "Monitor document",
    "report_draft_url": "Report draft",
    "report_final_pdf_url": "Final PDF draft",
    "report_final_odt_url": "Final ODT draft",
}

EXCLUDED_FIELDS = [
    "is_case_details_complete",
    "is_testing_details_complete",
    "is_reporting_details_complete",
    "is_report_correspondence_complete",
    "is_final_decision_complete",
    "is_enforcement_correspondence_complete",
]


@dataclass
class CaseFieldLabelAndValue:
    """Data to use in html table row of View case page"""

    value: Union[str, date]
    label: str
    type: str = "text"
    extra_label: str = ""
    DATE_TYPE: ClassVar[str] = "date"
    NOTES_TYPE: ClassVar[str] = "notes"
    URL_TYPE: ClassVar[str] = "url"
    TEXT_TYPE: ClassVar[str] = "text"


def extract_labels_and_values(
    case: Case,
    form: Union[
        CaseDetailUpdateForm,
        CaseTestResultsUpdateForm,
        CaseReportDetailsUpdateForm,
        CaseFinalDecisionUpdateForm,
    ],
) -> List[CaseFieldLabelAndValue]:
    """Extract field labels from form and values from case for use in html rows"""
    display_rows: List[CaseFieldLabelAndValue] = []
    for field_name, field in form.fields.items():
        if field_name in EXCLUDED_FIELDS:
            continue
        type_of_value = CaseFieldLabelAndValue.TEXT_TYPE
        value = getattr(case, field_name)
        if isinstance(value, User):
            value = value.get_full_name()
        elif isinstance(field, forms.ModelChoiceField):
            pass
        elif isinstance(field, forms.ChoiceField):
            value = getattr(case, f"get_{field_name}_display")()
        elif isinstance(field, AMPURLField):
            type_of_value = CaseFieldLabelAndValue.URL_TYPE
        elif isinstance(field, AMPTextField):
            type_of_value = CaseFieldLabelAndValue.NOTES_TYPE
        elif isinstance(value, date):
            type_of_value = CaseFieldLabelAndValue.DATE_TYPE
        display_rows.append(
            CaseFieldLabelAndValue(
                type=type_of_value,
                label=field.label,
                value=value,
                extra_label=EXTRA_LABELS.get(field_name, ""),
            )
        )
    return display_rows


def get_sent_date(
    form: CaseReportCorrespondenceUpdateForm, case_from_db: Case, sent_date_name: str
) -> Union[date, None]:
    """
    Work out what value to save in a sent date field on the case.
    If there is a new value in the form, don't replace an existing date on the database.
    If there is a new value in the form and no date on the database then use the date from the form.
    If there is no value in the form (i.e. the checkbox is unchecked), set the date on the database to None.
    """
    date_on_form: date = form.cleaned_data.get(sent_date_name)
    if date_on_form is None:
        return None
    date_on_db: date = getattr(case_from_db, sent_date_name)
    return date_on_db if date_on_db else date_on_form
