"""Common utility functions"""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum, auto
from typing import Any

from django import forms
from django.contrib.auth.models import User
from django.db import models

from .forms import AMPTextField, AMPURLField
from .models import Sector

EXCLUDED_FIELDS = [
    "version",
    "add_contact_email",
    "add_contact_notes",
    "report_draft_url",
]
EXTRA_LABELS = {
    "report_draft_url": "Report draft",
    "report_final_pdf_url": "Final draft (PDF)",
    "report_final_odt_url": "Final draft (ODT)",
}
PAGE_COMPLETE_DATE_SUFFIX: str = "_complete_date"


@dataclass
class FieldLabelAndValue:
    """Data to use in html table row of view details pages"""

    class Type(StrEnum):
        DATE = auto()
        NOTES = auto()
        URL = auto()
        TEXT = auto()

    value: str | date | None
    label: str | None
    type: Type = Type.TEXT
    extra_label: str = ""
    external_url: bool = True


def extract_form_labels_and_values(
    instance: models.Model,
    form: forms.Form,
) -> list[FieldLabelAndValue]:
    """Extract field labels from form and values from case for use in html rows"""
    display_rows: list[FieldLabelAndValue] = []
    if instance is None:
        return []
    for field_name, field in form.fields.items():
        if field_name in EXCLUDED_FIELDS or field_name.endswith(
            PAGE_COMPLETE_DATE_SUFFIX
        ):
            continue
        type_of_value: FieldLabelAndValue.Type = FieldLabelAndValue.Type.TEXT
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
            type_of_value: FieldLabelAndValue.Type = FieldLabelAndValue.Type.URL
        elif isinstance(field, AMPTextField):
            type_of_value: FieldLabelAndValue.Type = FieldLabelAndValue.Type.NOTES
        elif isinstance(value, date):
            type_of_value: FieldLabelAndValue.Type = FieldLabelAndValue.Type.DATE
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
