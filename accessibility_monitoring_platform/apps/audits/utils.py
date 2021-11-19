"""
Utilities for audits app
"""

from datetime import date
from typing import List, Union

from django import forms
from django.contrib.auth.models import User

from ..common.forms import AMPTextField, AMPURLField
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
    PAGE_TYPE_HOME,
    PAGE_TYPE_PDF,
    TEST_TYPE_PDF,
    TEST_TYPE_MANUAL,
)

EXTRA_LABELS = {}
EXCLUDED_FIELDS: List[str] = [
    "version",
    "audit_metadata_complete_date",
    "audit_pages_complete_date",
    "audit_manual_complete_date",
    "audit_axe_complete_date",
    "audit_pdf_complete_date",
    "audit_statement_1_complete_date",
    "audit_statement_2_complete_date",
    "audit_summary_complete_date",
    "manual_checks_complete_date",
    "axe_checks_complete_date",
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
        elif isinstance(field, AMPTextField):
            type_of_value = FieldLabelAndValue.NOTES_TYPE
        elif isinstance(field, AMPURLField):
            type_of_value = FieldLabelAndValue.URL_TYPE
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
    manual_wcag_definitions: List[WcagDefinition] = list(
        WcagDefinition.objects.filter(type=TEST_TYPE_MANUAL)
    )

    home_page: Union[Page, None] = None  # type: ignore
    for page_type in MANDATORY_PAGE_TYPES:
        page: Page = Page.objects.create(audit=audit, type=page_type)  # type: ignore
        record_model_create_event(user=user, model_object=page)  # type: ignore
        wcag_definitons: List[WcagDefinition] = (
            pdf_wcag_definitons
            if page_type == PAGE_TYPE_PDF
            else manual_wcag_definitions
        )
        for wcag_definition in wcag_definitons:
            check_result: CheckResult = CheckResult.objects.create(
                audit=audit,  # type: ignore
                page=page,
                type=wcag_definition.type,
                wcag_definition=wcag_definition,
            )
            record_model_create_event(user=user, model_object=check_result)  # type: ignore
        if page_type == PAGE_TYPE_HOME:
            home_page: Page = page
    audit.next_page = home_page  # type: ignore
    audit.save()


def create_check_results_for_new_page(page: Page, user: User) -> None:
    """
    Create mandatory check results for new page from WcagDefinition metadata.
    """
    manual_wcag_definitions: List[WcagDefinition] = list(
        WcagDefinition.objects.filter(type=TEST_TYPE_MANUAL)
    )

    for wcag_definition in manual_wcag_definitions:
        check_result: CheckResult = CheckResult.objects.create(
            audit=page.audit,
            page=page,
            type=wcag_definition.type,
            wcag_definition=wcag_definition,
        )
        record_model_create_event(user=user, model_object=check_result)  # type: ignore
