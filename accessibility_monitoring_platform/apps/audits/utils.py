"""
Utilities for audits app
"""

from typing import Dict, Tuple, List

from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.urls import reverse

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
    CheckResultUpdateForm,
)
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


def get_audit_url(url_name: str, audit: Audit) -> str:
    """Return url string for name and audit"""
    return reverse(
        f"audits:{url_name}",
        kwargs={
            "pk": audit.id,  # type: ignore
            "case_id": audit.case.id,  # type: ignore
        },
    )


def create_pages_and_checks_for_new_audit(audit: Audit) -> None:
    """
    Create mandatory pages for new audit.
    Create Wcag tests from WcagDefinition metadata for new audit.
    """

    for page_type in MANDATORY_PAGE_TYPES:
        page: Page = Page.objects.create(audit=audit, type=page_type)  # type: ignore
        test_type: str = (
            TEST_TYPE_PDF if page_type == PAGE_TYPE_PDF else TEST_TYPE_MANUAL
        )
        create_check_results_for_new_page(page=page, test_type=test_type)
    audit.next_page = Page.objects.get(audit=audit, type=PAGE_TYPE_HOME)  # type: ignore
    audit.save()


def create_check_results_for_new_page(
    page: Page, test_type: str = TEST_TYPE_MANUAL
) -> None:
    """
    Create mandatory check results for new page from WcagDefinition metadata.
    """
    manual_wcag_definitions: QuerySet[WcagDefinition] = WcagDefinition.objects.filter(
        type=test_type
    )

    for wcag_definition in manual_wcag_definitions:
        CheckResult.objects.create(
            audit=page.audit,
            page=page,
            type=wcag_definition.type,
            wcag_definition=wcag_definition,
        )


def copy_all_pages_check_results(
    user: User, audit: Audit, check_results: List[CheckResult]
):
    """Copy check results from the All pages page to other html pages"""
    for page in audit.html_pages:
        for check_result in check_results:
            other_check_result, created = CheckResult.objects.get_or_create(  # type: ignore
                audit=audit,
                page=page,
                wcag_definition=check_result.wcag_definition,
            )
            other_check_result.failed = check_result.failed
            other_check_result.type = check_result.type
            other_check_result.notes = check_result.notes
            if not created:
                record_model_update_event(user=user, model_object=check_result)
            other_check_result.save()
            if created:
                record_model_create_event(user=user, model_object=check_result)


def get_audit_metadata_rows(audit: Audit) -> List[FieldLabelAndValue]:
    """Build Test view page table rows from audit metadata"""
    rows: List[FieldLabelAndValue] = extract_form_labels_and_values(
        instance=audit,
        form=AuditMetadataUpdateForm(),  # type: ignore
    )
    if audit.case.auditor:
        rows.insert(
            1,
            FieldLabelAndValue(
                label="Auditor",
                value=audit.case.auditor.get_full_name(),
            ),
        )
    return rows


def get_audit_pdf_rows(audit: Audit) -> List[FieldLabelAndValue]:
    """Build Test view page table rows from audit pdf failures"""
    return [
        FieldLabelAndValue(
            label=check_result.wcag_definition.name,
            value=check_result.notes,
            type=FieldLabelAndValue.NOTES_TYPE,
        )
        for check_result in audit.failed_pdf_check_results
    ]


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
    return statement_1_rows + statement_2_rows


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


def group_check_results_by_wcag_sub_type_labels(
    check_result_update_forms: List[CheckResultUpdateForm],
) -> List[Tuple[str, List[CheckResultUpdateForm]]]:
    """
    Group check result forms by wcag/check sub-type and then return list of tuples
    of sub-type labels and list of forms of that sub-type.
    """
    check_result_forms_by_wcag_sub_type: Dict[str, List[CheckResultUpdateForm]] = {}

    for check_result_form in check_result_update_forms:
        sub_type_label: str = MANUAL_CHECK_SUB_TYPE_LABELS[
            check_result_form.instance.wcag_definition.sub_type
        ]
        if sub_type_label in check_result_forms_by_wcag_sub_type:
            check_result_forms_by_wcag_sub_type[sub_type_label].append(
                check_result_form
            )
        else:
            check_result_forms_by_wcag_sub_type[sub_type_label] = [check_result_form]
    return [(key, value) for key, value in check_result_forms_by_wcag_sub_type.items()]


def group_check_results_by_wcag(
    check_results: QuerySet[CheckResult],
) -> List[Tuple[WcagDefinition, List[CheckResult]]]:
    """
    Group check results by wcag definition and then return list of tuples
    of wcag definition and list of check results of that wcag definiton.
    """
    audit_failures_by_wcag: Dict[WcagDefinition, List[CheckResult]] = {}

    for check_result in check_results:
        if check_result.wcag_definition in audit_failures_by_wcag:
            audit_failures_by_wcag[check_result.wcag_definition].append(check_result)
        else:
            audit_failures_by_wcag[check_result.wcag_definition] = [check_result]

    return [(key, value) for key, value in audit_failures_by_wcag.items()]


def group_check_results_by_page(
    check_results: QuerySet[CheckResult],
) -> List[Tuple[Page, List[CheckResult]]]:
    """
    Group check results by page and then return list of tuples
    of page and list of check results of that page.
    """
    audit_failures_by_page: Dict[Page, List[CheckResult]] = {}

    for check_result in check_results:
        if check_result.page in audit_failures_by_page:
            audit_failures_by_page[check_result.page].append(check_result)
        else:
            audit_failures_by_page[check_result.page] = [check_result]

    return [(key, value) for key, value in audit_failures_by_page.items()]
