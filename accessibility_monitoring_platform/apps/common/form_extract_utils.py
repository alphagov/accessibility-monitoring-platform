""" Common utility functions """

from dataclasses import dataclass
from datetime import date
from typing import Any, ClassVar

from django import forms
from django.contrib.auth.models import User
from django.db import models

from .forms import AMPTextField, AMPURLField
from .models import Sector

EXCLUDED_FIELDS = [
    "version",
    "case_details_complete_date",
    "testing_details_complete_date",
    "reporting_details_complete_date",
    "qa_auditor_complete_date",
    "cores_overview_complete_date",
    "manage_contact_details_complete_date",
    "report_sent_on_complete_date",
    "one_week_followup_complete_date",
    "four_week_followup_complete_date",
    "report_acknowledged_complete_date",
    "twelve_week_update_requested_complete_date",
    "one_week_followup_final_complete_date",
    "twelve_week_update_request_ack_complete_date",
    "report_correspondence_complete_date",
    "final_decision_complete_date",
    "enforcement_correspondence_complete_date",
    "audit_metadata_complete_date",
    "audit_pages_complete_date",
    "audit_manual_complete_date",
    "audit_axe_complete_date",
    "audit_pdf_complete_date",
    "archive_audit_statement_1_complete_date",
    "archive_audit_statement_2_complete_date",
    "audit_wcag_summary_complete_date",
    "audit_statement_summary_complete_date",
    "manual_checks_complete_date",
    "axe_checks_complete_date",
    "case_close_complete_date",
    "post_case_complete_date",
    "review_changes_complete_date",
    "twelve_week_correspondence_complete_date",
    "twelve_week_retest_complete_date",
    "add_contact_email",
    "add_contact_notes",
    "initial_disproportionate_burden_complete_date",
    "twelve_week_disproportionate_burden_complete_date",
    "audit_retest_metadata_complete_date",
    "report_draft_url",
]
EXTRA_LABELS = {
    "report_draft_url": "Report draft",
    "report_final_pdf_url": "Final draft (PDF)",
    "report_final_odt_url": "Final draft (ODT)",
}


@dataclass
class FieldLabelAndValue:
    """Data to use in html table row of view details pages"""

    value: str | date | None
    label: str | None
    type: str = "text"
    extra_label: str = ""
    external_url: bool = True
    DATE_TYPE: ClassVar[str] = "date"
    NOTES_TYPE: ClassVar[str] = "notes"
    URL_TYPE: ClassVar[str] = "url"
    TEXT_TYPE: ClassVar[str] = "text"


def extract_form_labels_and_values(  # noqa: C901
    instance: models.Model,
    form: type[forms.Form],
    excluded_fields: list[str] | None = None,
) -> list[FieldLabelAndValue]:
    """Extract field labels from form and values from case for use in html rows"""
    display_rows: list[FieldLabelAndValue] = []
    if excluded_fields is None:
        excluded_fields = []
    for field_name, field in form.fields.items():
        if field_name in EXCLUDED_FIELDS:
            continue
        if field_name in excluded_fields:
            continue
        type_of_value: str = FieldLabelAndValue.TEXT_TYPE
        value: Any = getattr(instance, field_name)
        if isinstance(value, User):
            value = value.get_full_name()
        elif field_name == "sector" and value is None:
            value = "Unknown"
        elif isinstance(value, Sector):
            value = str(value)
        elif isinstance(field, forms.ModelChoiceField):
            pass
        elif isinstance(field, forms.ChoiceField):
            value = getattr(instance, f"get_{field_name}_display")()
        elif isinstance(field, AMPURLField):
            type_of_value = FieldLabelAndValue.URL_TYPE
        elif isinstance(field, AMPTextField):
            type_of_value = FieldLabelAndValue.NOTES_TYPE
        elif isinstance(value, date):
            type_of_value = FieldLabelAndValue.DATE_TYPE
        if field.label == "Notes" and not value:
            continue
        display_rows.append(
            FieldLabelAndValue(
                type=type_of_value,
                label=field.label,
                value=value,
                extra_label=EXTRA_LABELS.get(field_name, ""),
            )
        )
    return display_rows
