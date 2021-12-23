"""
Utilities for audits app
"""

from typing import Dict, List, Union

from django.contrib.auth.models import User

from ..common.utils import record_model_create_event, record_model_update_event
from ..common.form_extract_utils import (
    extract_form_labels_and_values,
    FieldLabelAndValue,
)
from .forms import (
    AuditMetadataUpdateForm,
    AuditStatement1UpdateForm,
    AuditStatement2UpdateForm,
    AuditReportOptionsUpdateForm,
    CheckResultForm,
)
from .models import (
    Audit,
    Page,
    WcagDefinition,
    CheckResult,
    CHECK_RESULT_NOT_TESTED,
    REPORT_ACCESSIBILITY_ISSUE_TEXT,
    REPORT_NEXT_ISSUE_TEXT,
)

MANUAL_CHECK_SUB_TYPE_LABELS: Dict[str, str] = {
    "keyboard": "Keyboard",
    "zoom": "Zoom and Reflow",
    "audio-visual": "Audio and Visual",
    "additional": "Additional",
    "other": "Other",
}


def copy_all_pages_check_results(user: User, page: Page):
    """Copy check results from the All pages page to other html pages"""
    for destination_page in page.audit.html_pages:
        for check_result in page.all_check_results:
            other_check_result, created = CheckResult.objects.get_or_create(  # type: ignore
                audit=page.audit,
                page=destination_page,
                wcag_definition=check_result.wcag_definition,
            )
            other_check_result.check_result_state = check_result.check_result_state
            other_check_result.type = check_result.type
            other_check_result.notes = check_result.notes
            if created:
                other_check_result.save()
                record_model_create_event(user=user, model_object=check_result)
            else:
                record_model_update_event(user=user, model_object=check_result)
                other_check_result.save()


def get_audit_metadata_rows(audit: Audit) -> List[FieldLabelAndValue]:
    """Build Test view page table rows from audit metadata"""
    rows: List[FieldLabelAndValue] = extract_form_labels_and_values(
        instance=audit,
        form=AuditMetadataUpdateForm(),  # type: ignore
    )
    return rows


def get_audit_statement_rows(audit: Audit) -> List[FieldLabelAndValue]:
    """Build Test view page table rows from audit statement checks"""
    statement_1_rows: List[FieldLabelAndValue] = extract_form_labels_and_values(
        instance=audit,
        form=AuditStatement1UpdateForm(),  # type: ignore
    )
    statement_2_rows: List[FieldLabelAndValue] = extract_form_labels_and_values(
        instance=audit,
        form=AuditStatement2UpdateForm(),  # type: ignore
    )
    return (
        statement_1_rows + statement_2_rows[1:]
    )  # Skip first field as it echoes first form


def get_audit_report_options_rows(audit: Audit) -> List[FieldLabelAndValue]:
    """Build Test view page table rows from audit report options"""
    accessibility_statement_state_row: FieldLabelAndValue = FieldLabelAndValue(
        label=AuditReportOptionsUpdateForm.base_fields[
            "accessibility_statement_state"
        ].label,
        value=audit.get_accessibility_statement_state_display(),  # type: ignore
    )
    accessibility_statement_issues_rows: List[FieldLabelAndValue] = [
        FieldLabelAndValue(
            label=label,
            value=getattr(audit, f"get_{field_name}_display")(),
        )
        for field_name, label in REPORT_ACCESSIBILITY_ISSUE_TEXT.items()
    ]
    report_options_next_row: FieldLabelAndValue = FieldLabelAndValue(
        label=AuditReportOptionsUpdateForm.base_fields["report_options_next"].label,
        value=audit.get_report_options_next_display(),  # type: ignore
    )
    report_next_issues_rows: List[FieldLabelAndValue] = [
        FieldLabelAndValue(
            label=label,
            value=getattr(audit, f"get_{field_name}_display")(),
        )
        for field_name, label in REPORT_NEXT_ISSUE_TEXT.items()
    ]
    return (
        [accessibility_statement_state_row]
        + accessibility_statement_issues_rows
        + [report_options_next_row]
        + report_next_issues_rows
    )


def create_or_update_check_results_for_page(
    user: User, page: Page, check_result_forms: List[CheckResultForm]
) -> None:
    """
    Create or update check results based on form data:

    If a check result matching the WCAG definition does not exist and the user
    has changed the check state from the default value or entered notes then
    create a check result.

    if a check result matching the WCAG definition does exist then apply the
    latest state and notes values.
    """
    for check_result_form in check_result_forms:
        wcag_definition: WcagDefinition = check_result_form.cleaned_data[
            "wcag_definition"
        ]
        check_result_state: str = check_result_form.cleaned_data["check_result_state"]
        notes: str = check_result_form.cleaned_data["notes"]
        if wcag_definition in page.check_results_by_wcag_definition:
            check_result: CheckResult = page.check_results_by_wcag_definition[
                wcag_definition
            ]
            check_result.check_result_state = check_result_state
            check_result.notes = notes
            record_model_update_event(user=user, model_object=check_result)
            check_result.save()
        elif notes != "" or check_result_state != CHECK_RESULT_NOT_TESTED:
            check_result: CheckResult = CheckResult.objects.create(
                audit=page.audit,
                page=page,
                wcag_definition=wcag_definition,
                type=wcag_definition.type,
                check_result_state=check_result_state,
                notes=notes,
            )
            record_model_create_event(user=user, model_object=check_result)


def get_all_possible_check_results_for_page(
    page: Page, wcag_definitions: List[WcagDefinition]
) -> List[Dict[str, Union[str, WcagDefinition]]]:
    """
    Combine exisiting check result with all the WCAG definitions
    to create a list of dictionaries for use in populating the
    CheckResultFormset with all possible results.
    """
    check_results_by_wcag_definition: Dict[
        WcagDefinition, CheckResult
    ] = page.check_results_by_wcag_definition
    check_results: List[Dict[str, Union[str, WcagDefinition]]] = []

    for wcag_definition in wcag_definitions:
        if wcag_definition in check_results_by_wcag_definition:
            check_result: CheckResult = check_results_by_wcag_definition[
                wcag_definition
            ]
            check_result_state: str = check_result.check_result_state
            notes: str = check_result.notes
        else:
            check_result_state: str = CHECK_RESULT_NOT_TESTED
            notes: str = ""
        check_results.append(
            {
                "wcag_definition": wcag_definition,
                "check_result_state": check_result_state,
                "notes": notes,
            }
        )
    return check_results
