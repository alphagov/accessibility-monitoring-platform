"""
Utilities for audits app
"""

from datetime import date
from typing import List

from django import forms
from django.contrib.auth.models import User

from ..common.utils import (
    FieldLabelAndValue,
    record_model_create_event,
)
from .forms import AuditUpdateMetadataForm
from .models import (
    Audit,
    Page,
    WcagDefinition,
    CheckResult,
    MANDATORY_PAGE_TYPES,
    PAGE_TYPE_PDF,
    TEST_TYPE_PDF,
)

EXTRA_LABELS = {}
EXCLUDED_FIELDS: List[str] = [
    "version",
    "audit_metadata_complete_date",
    "audit_pages_complete_date",
    "audit_manual_complete_date",
    "audit_axe_complete_date",
    "audit_pdf_complete_date",
]


def extract_labels_and_values(
    audit: Audit,
    form: AuditUpdateMetadataForm,
) -> List[FieldLabelAndValue]:
    """Extract field labels from form and values from case for use in html rows"""
    display_rows: List[FieldLabelAndValue] = []
    for field_name, field in form.fields.items():
        if field_name in EXCLUDED_FIELDS:
            continue
        type_of_value = FieldLabelAndValue.TEXT_TYPE
        value = getattr(audit, field_name)
        if isinstance(field, forms.ModelChoiceField):
            pass
        elif isinstance(field, forms.ChoiceField):
            value = getattr(audit, f"get_{field_name}_display")()
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


def create_pages_and_tests_for_new_audit(audit: Audit, user: User) -> None:
    """
    Create mandatory pages for new audit.
    Create Wcag tests from WcagDefinition metadata for new audit.
    """
    pdf_wcag_definitons: List[WcagDefinition] = list(
        WcagDefinition.objects.filter(type=TEST_TYPE_PDF)
    )
    non_pdf_wcag_definitons: List[WcagDefinition] = list(
        WcagDefinition.objects.exclude(type=TEST_TYPE_PDF)
    )

    for page_type in MANDATORY_PAGE_TYPES:
        page: Page = Page.objects.create(audit=audit, type=page_type)  # type: ignore
        record_model_create_event(user=user, model_object=page)  # type: ignore
        wcag_definitons: List[WcagDefinition] = (
            pdf_wcag_definitons
            if page_type == PAGE_TYPE_PDF
            else non_pdf_wcag_definitons
        )
        for wcag_definition in wcag_definitons:
            check_result: CheckResult = CheckResult.objects.create(
                audit=audit,  # type: ignore
                page=page,
                type=wcag_definition.type,
                wcag_definition=wcag_definition,
            )
            record_model_create_event(user=user, model_object=check_result)  # type: ignore
