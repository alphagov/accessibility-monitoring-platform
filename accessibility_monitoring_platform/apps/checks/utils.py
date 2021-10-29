"""
Utilities for checks app
"""

from datetime import date
from typing import List

from django import forms

from .forms import CheckUpdateMetadataForm
from .models import Check

from ..common.utils import FieldLabelAndValue

EXTRA_LABELS = {}
EXCLUDED_FIELDS: List[str] = [
    "version",
    "check_metadata_complete_date",
    "check_pages_complete_date",
    "check_manual_complete_date",
    "check_axe_complete_date",
    "check_pdf_complete_date",
]


def extract_labels_and_values(
    check: Check,
    form: CheckUpdateMetadataForm,
) -> List[FieldLabelAndValue]:
    """Extract field labels from form and values from case for use in html rows"""
    display_rows: List[FieldLabelAndValue] = []
    for field_name, field in form.fields.items():
        if field_name in EXCLUDED_FIELDS:
            continue
        type_of_value = FieldLabelAndValue.TEXT_TYPE
        value = getattr(check, field_name)
        if isinstance(field, forms.ModelChoiceField):
            pass
        elif isinstance(field, forms.ChoiceField):
            value = getattr(check, f"get_{field_name}_display")()
        elif isinstance(value, date):
            type_of_value = FieldLabelAndValue.DATE_TYPE
        display_rows.append(
            FieldLabelAndValue(
                type=type_of_value,
                label=field.label,
                value=value,
                extra_label=EXTRA_LABELS.get(field_name, ""),
            )
        )
    return display_rows
