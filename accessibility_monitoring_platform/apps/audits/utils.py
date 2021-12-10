"""
Utilities for audits app
"""

from typing import Dict, Tuple, List

from django.contrib.auth.models import User
from django.db.models.query import QuerySet

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
)
from .models import (
    Audit,
    Page,
    WcagDefinition,
    CheckResult,
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


def group_check_results_by_page(
    check_results: QuerySet[CheckResult],
) -> List[Tuple[Page, List[CheckResult]]]:
    """
    Group check results by page and then return list of tuples
    of page and list of check results of that page.
    """
    check_results_by_page: Dict[Page, List[CheckResult]] = {}

    for check_result in check_results:
        if check_result.page in check_results_by_page:
            check_results_by_page[check_result.page].append(check_result)
        else:
            check_results_by_page[check_result.page] = [check_result]

    return [(key, value) for key, value in check_results_by_page.items()]


def group_check_results_by_wcag(
    check_results: QuerySet[CheckResult],
) -> List[Tuple[WcagDefinition, List[CheckResult]]]:
    """
    Group check results by wcag definition and then return list of tuples
    of wcag definition and list of check results of that wcag definiton.
    """
    check_results_by_wcag: Dict[WcagDefinition, List[CheckResult]] = {}

    for check_result in check_results:
        if check_result.wcag_definition in check_results_by_wcag:
            check_results_by_wcag[check_result.wcag_definition].append(check_result)
        else:
            check_results_by_wcag[check_result.wcag_definition] = [check_result]

    return [(key, value) for key, value in check_results_by_wcag.items()]
