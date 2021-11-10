"""
Utilities for checks app
"""

from datetime import date
from typing import List

from django import forms
from django.contrib.auth.models import User
from django.db.models.query import QuerySet

from ..common.utils import (
    FieldLabelAndValue,
    record_model_create_event,
)
from .forms import CheckUpdateMetadataForm
from .models import (
    Check,
    Page,
    WcagTest,
    CheckTest,
    MANDATORY_PAGE_TYPES,
)

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


def create_pages_and_tests_for_new_check(parent_check: Check, user: User) -> None:
    """
    Create mandatory pages for new check.
    Create Wcag tests from WcagTest metadata for new check.
    """
    for page_type in MANDATORY_PAGE_TYPES:
        page: Page = Page.objects.create(parent_check=parent_check, type=page_type)  # type: ignore
        record_model_create_event(user=user, model_object=page)  # type: ignore
    wcag_tests: QuerySet[WcagTest] = WcagTest.objects.all()
    for wcag_test in wcag_tests:
        check_test: CheckTest = CheckTest.objects.create(
            parent_check=parent_check,  # type: ignore
            type=wcag_test.type,
            wcag_test=wcag_test,
        )
        record_model_create_event(user=user, model_object=check_test)  # type: ignore
