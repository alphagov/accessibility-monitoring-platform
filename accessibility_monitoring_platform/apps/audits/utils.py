"""
Utilities for audits app
"""

from typing import Dict, Tuple, List, Union

from django.contrib.auth.models import User
from django.db.models.query import QuerySet

from ..common.models import BOOLEAN_TRUE
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
    MANDATORY_PAGE_TYPES,
    PAGE_TYPE_ALL,
    PAGE_TYPE_HOME,
    PAGE_TYPE_PDF,
    TEST_TYPE_PDF,
    TEST_TYPE_MANUAL,
    REPORT_ACCESSIBILITY_ISSUE_TEXT,
    REPORT_NEXT_ISSUE_TEXT,
)


def create_pages_and_checks_for_new_audit(audit: Audit, user: User) -> None:
    """
    Create mandatory pages for new audit.
    Create Wcag tests from WcagDefinition metadata for new audit.
    """

    home_page: Union[Page, None] = None  # type: ignore
    for page_type in MANDATORY_PAGE_TYPES:
        page: Page = Page.objects.create(audit=audit, type=page_type)  # type: ignore
        record_model_create_event(user=user, model_object=page)  # type: ignore
        test_type: str = (
            TEST_TYPE_PDF if page_type == PAGE_TYPE_PDF else TEST_TYPE_MANUAL
        )
        create_check_results_for_new_page(page=page, user=user, test_type=test_type)
        if page_type == PAGE_TYPE_HOME:
            home_page: Page = page
    audit.next_page = home_page  # type: ignore
    audit.save()


def create_check_results_for_new_page(
    page: Page, user: User, test_type: str = TEST_TYPE_MANUAL
) -> None:
    """
    Create mandatory check results for new page from WcagDefinition metadata.
    """
    manual_wcag_definitions: QuerySet[WcagDefinition] = WcagDefinition.objects.filter(
        type=test_type
    )

    for wcag_definition in manual_wcag_definitions:
        check_result: CheckResult = CheckResult.objects.create(
            audit=page.audit,
            page=page,
            type=wcag_definition.type,
            wcag_definition=wcag_definition,
        )
        record_model_create_event(user=user, model_object=check_result)  # type: ignore


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


def get_audit_check_results_by_wcag(
    audit: Audit, test_type: str
) -> List[Tuple[WcagDefinition, List[CheckResult]]]:
    """
    Build list of check results grouped by WCAG definitons for use
    in accordion on Test view page.
    """
    check_results: QuerySet[CheckResult] = (
        CheckResult.objects.filter(audit=audit, type=test_type, failed=BOOLEAN_TRUE)
        .exclude(page__type=PAGE_TYPE_ALL)
        .order_by("wcag_definition__id")
    )
    check_result_by_wcag: Dict[WcagDefinition, List[CheckResult]] = {}
    for check_result in check_results:
        if check_result.wcag_definition in check_result_by_wcag:
            check_result_by_wcag[check_result.wcag_definition].append(check_result)
        else:
            check_result_by_wcag[check_result.wcag_definition] = [check_result]
    return [(key, value) for key, value in check_result_by_wcag.items()]


def get_audit_pdf_rows(audit: Audit) -> List[FieldLabelAndValue]:
    """Build Test view page table rows from audit pdf failures"""
    check_results: QuerySet[CheckResult] = CheckResult.objects.filter(
        audit=audit, type=TEST_TYPE_PDF, failed=BOOLEAN_TRUE
    )
    return [
        FieldLabelAndValue(
            label=check_result.wcag_definition.name,
            value=check_result.notes,
            type=FieldLabelAndValue.NOTES_TYPE,
        )
        for check_result in check_results
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
