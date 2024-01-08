"""
Utilities for audits app
"""

from datetime import date, datetime
from functools import partial
from typing import Callable, Dict, List, Optional, Union

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from ..cases.models import Case
from ..common.form_extract_utils import (
    FieldLabelAndValue,
    extract_form_labels_and_values,
)
from ..common.utils import record_model_create_event, record_model_update_event
from .forms import (
    ArchiveAuditReportOptionsUpdateForm,
    ArchiveAuditStatement1UpdateForm,
    ArchiveAuditStatement2UpdateForm,
    ArchiveCaseComplianceStatement12WeekUpdateForm,
    ArchiveCaseComplianceStatementInitialUpdateForm,
    AuditMetadataUpdateForm,
    CaseComplianceWebsite12WeekUpdateForm,
    CaseComplianceWebsiteInitialUpdateForm,
    CheckResultForm,
)
from .models import (
    ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT,
    ARCHIVE_REPORT_NEXT_ISSUE_TEXT,
    CHECK_RESULT_NOT_TESTED,
    MANDATORY_PAGE_TYPES,
    PAGE_TYPE_HOME,
    Audit,
    CheckResult,
    Page,
    Retest,
    RetestCheckResult,
    RetestPage,
    StatementCheck,
    StatementCheckResult,
    WcagDefinition,
)

MANUAL_CHECK_SUB_TYPE_LABELS: Dict[str, str] = {
    "keyboard": "Keyboard",
    "zoom": "Zoom and Reflow",
    "audio-visual": "Audio and Visual",
    "additional": "Additional",
    "other": "Other",
}


def get_audit_report_options_rows(audit: Audit) -> List[FieldLabelAndValue]:
    """Build Test view page table rows from audit report options"""
    archive_accessibility_statement_state_row: FieldLabelAndValue = FieldLabelAndValue(
        label=ArchiveAuditReportOptionsUpdateForm.base_fields[
            "archive_accessibility_statement_state"
        ].label,
        value=audit.get_archive_accessibility_statement_state_display(),
    )
    archive_accessibility_statement_issues_rows: List[FieldLabelAndValue] = [
        FieldLabelAndValue(
            label=label,
            value=getattr(audit, f"get_{field_name}_display")(),
        )
        for field_name, label in ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT.items()
    ]
    archive_accessibility_statement_report_text_wording_row: FieldLabelAndValue = (
        FieldLabelAndValue(
            label=ArchiveAuditReportOptionsUpdateForm.base_fields[
                "archive_accessibility_statement_report_text_wording"
            ].label,
            value=audit.archive_accessibility_statement_report_text_wording,
            type=FieldLabelAndValue.NOTES_TYPE,
        )
    )
    archive_report_options_next_row: FieldLabelAndValue = FieldLabelAndValue(
        label=ArchiveAuditReportOptionsUpdateForm.base_fields[
            "archive_report_options_next"
        ].label,
        value=audit.get_archive_report_options_next_display(),
    )
    archive_report_next_issues_rows: List[FieldLabelAndValue] = [
        FieldLabelAndValue(
            label=label,
            value=getattr(audit, f"get_{field_name}_display")(),
        )
        for field_name, label in ARCHIVE_REPORT_NEXT_ISSUE_TEXT.items()
    ]
    archive_report_options_notes: FieldLabelAndValue = FieldLabelAndValue(
        label=ArchiveAuditReportOptionsUpdateForm.base_fields[
            "archive_report_options_notes"
        ].label,
        value=audit.archive_report_options_notes,
        type=FieldLabelAndValue.NOTES_TYPE,
    )
    return (
        [archive_accessibility_statement_state_row]
        + archive_accessibility_statement_issues_rows
        + [
            archive_accessibility_statement_report_text_wording_row,
            archive_report_options_next_row,
        ]
        + archive_report_next_issues_rows
        + [archive_report_options_notes]
    )


def get_test_view_tables_context(audit: Audit) -> Dict[str, List[FieldLabelAndValue]]:
    """Get context for test view tables"""
    get_audit_rows: Callable = partial(extract_form_labels_and_values, instance=audit)
    get_compliance_rows: Callable = partial(
        extract_form_labels_and_values, instance=audit.case.compliance
    )
    return {
        "audit_metadata_rows": get_audit_rows(form=AuditMetadataUpdateForm()),
        "website_decision_rows": get_compliance_rows(
            form=CaseComplianceWebsiteInitialUpdateForm()
        ),
        "audit_statement_1_rows": get_audit_rows(
            form=ArchiveAuditStatement1UpdateForm()
        ),
        "audit_statement_2_rows": get_audit_rows(
            form=ArchiveAuditStatement2UpdateForm()
        ),
        "statement_decision_rows": get_compliance_rows(
            form=ArchiveCaseComplianceStatementInitialUpdateForm()
        ),
        "audit_report_options_rows": get_audit_report_options_rows(audit=audit),
    }


def get_retest_view_tables_context(case: Case) -> Dict[str, List[FieldLabelAndValue]]:
    """Get context for 12-week retest view tables"""
    get_compliance_rows: Callable = partial(
        extract_form_labels_and_values, instance=case.compliance
    )
    return {
        "audit_retest_website_decision_rows": get_compliance_rows(
            form=CaseComplianceWebsite12WeekUpdateForm()
        ),
        "audit_retest_statement_decision_rows": get_compliance_rows(
            form=ArchiveCaseComplianceStatement12WeekUpdateForm()
        ),
    }


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
            if (
                check_result.check_result_state != check_result_state
                or check_result.notes != notes
            ):
                check_result.check_result_state = check_result_state
                check_result.notes = notes
                record_model_update_event(user=user, model_object=check_result)
                report_data_updated(audit=check_result.audit)
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
            report_data_updated(audit=page.audit)


def get_all_possible_check_results_for_page(
    page: Page, wcag_definitions: List[WcagDefinition]
) -> List[Dict[str, Union[str, WcagDefinition]]]:
    """
    Combine existing check result with all the WCAG definitions
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


def create_mandatory_pages_for_new_audit(audit: Audit) -> None:
    """
    Create mandatory pages for new audit.
    """

    for page_type in MANDATORY_PAGE_TYPES:
        if page_type == PAGE_TYPE_HOME:
            Page.objects.create(
                audit=audit, page_type=page_type, url=audit.case.home_page_url
            )
        else:
            Page.objects.create(audit=audit, page_type=page_type)


def create_statement_checks_for_new_audit(audit: Audit) -> None:
    """
    Create statement check results for new audit.
    """
    today: date = date.today()
    for statement_check in StatementCheck.objects.on_date(today):
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
        )


def get_next_page_url(audit: Audit, current_page: Union[Page, None] = None) -> str:
    """
    Return the path of the page to go to when a save and continue button is
    pressed on the page where pages or pages check results are entered.
    """
    audit_pk: Dict[str, int] = {"pk": audit.id}
    if not audit.testable_pages:
        return reverse("audits:edit-website-decision", kwargs=audit_pk)

    if current_page is None:
        next_page_pk: Dict[str, int] = {"pk": audit.testable_pages.first().id}
        return reverse("audits:edit-audit-page-checks", kwargs=next_page_pk)

    testable_pages: List[Page] = list(audit.testable_pages)
    if testable_pages[-1] == current_page:
        return reverse("audits:edit-website-decision", kwargs=audit_pk)

    current_page_position: int = testable_pages.index(current_page)
    next_page_pk: Dict[str, int] = {"pk": testable_pages[current_page_position + 1].id}
    return reverse("audits:edit-audit-page-checks", kwargs=next_page_pk)


def get_next_retest_page_url(
    audit: Audit, current_page: Union[Page, None] = None
) -> str:
    """
    Return the path of the page to go to when a save and continue button is
    pressed on the page where pages or pages check results are retested.
    """
    audit_pk: Dict[str, int] = {"pk": audit.id}
    testable_pages_with_errors: List[Page] = [
        page for page in audit.testable_pages if page.failed_check_results
    ]
    if not testable_pages_with_errors:
        return reverse("audits:edit-audit-retest-pages", kwargs=audit_pk)

    if current_page is None:
        next_page_pk: Dict[str, int] = {"pk": testable_pages_with_errors[0].id}
        return reverse("audits:edit-audit-retest-page-checks", kwargs=next_page_pk)

    if testable_pages_with_errors[-1] == current_page:
        return reverse("audits:edit-audit-retest-pages", kwargs=audit_pk)

    current_page_position: int = testable_pages_with_errors.index(current_page)
    next_page_pk: Dict[str, int] = {
        "pk": testable_pages_with_errors[current_page_position + 1].id
    }
    return reverse("audits:edit-audit-retest-page-checks", kwargs=next_page_pk)


def other_page_failed_check_results(
    page: Page,
) -> Dict[WcagDefinition, List[CheckResult]]:
    """
    Find all failed check results for other pages.
    Return them in a dictionary keyed by their WcagDefinitions.

    Args:
        page (Page): Page object

    Returns:
        Dict[WcagDefinition, List[CheckResult]]: Dictionary of failed check results
    """
    failed_check_results_by_wcag_definition: Dict[
        WcagDefinition, List[CheckResult]
    ] = {}
    for check_result in page.audit.failed_check_results.exclude(page=page):
        if check_result.wcag_definition in failed_check_results_by_wcag_definition:
            failed_check_results_by_wcag_definition[
                check_result.wcag_definition
            ].append(check_result)
        else:
            failed_check_results_by_wcag_definition[check_result.wcag_definition] = [
                check_result
            ]
    return failed_check_results_by_wcag_definition


def report_data_updated(audit: Audit) -> None:
    """Record when an update changing report content as occurred."""
    now: datetime = timezone.now()
    audit.published_report_data_updated_time = now
    audit.save()


def create_checkresults_for_retest(retest: Retest) -> None:
    """
    Create pages and checkresults for restest from outstanding issues of previous test.
    """

    audit: Audit = retest.case.audit
    if retest.id_within_case == 1:
        # Create fake retest from 12-week results for first retest to compare itself to
        retest_0: Retest = Retest.objects.create(case=retest.case, id_within_case=0)
        for page in audit.testable_pages:
            if page.unfixed_check_results:
                retest_page: RetestPage = RetestPage.objects.create(
                    retest=retest_0, page=page
                )
                for check_result in page.unfixed_check_results:
                    RetestCheckResult.objects.create(
                        retest=retest_0,
                        retest_page=retest_page,
                        check_result=check_result,
                        retest_state=check_result.retest_state,
                        retest_notes=check_result.retest_notes,
                    )

    previous_retest: Retest = retest.case.retests.filter(
        id_within_case=retest.id_within_case - 1
    ).first()

    for previous_retest_page in RetestPage.objects.filter(retest=previous_retest):
        retest_page: RetestPage = RetestPage.objects.create(
            retest=retest,
            page=previous_retest_page.page,
            missing_date=previous_retest_page.missing_date,
        )
        for previous_retest_check_result in previous_retest_page.unfixed_check_results:
            RetestCheckResult.objects.create(
                retest=retest,
                retest_page=retest_page,
                check_result=previous_retest_check_result.check_result,
            )


def get_next_equality_body_retest_page_url(
    retest: Retest, current_page: Optional[RetestPage] = None
) -> str:
    """
    Return the path of the next retest page to go to when a save and continue button is
    pressed.
    """
    retest_pk: Dict[str, int] = {"pk": retest.id}
    retest_pages: List[RetestPage] = list(retest.retestpage_set.all())
    if not retest_pages:
        return reverse("audits:retest-comparison-update", kwargs=retest_pk)

    if current_page is None:
        next_page_pk: Dict[str, int] = {"pk": retest_pages[0].id}
        return reverse("audits:edit-retest-page-checks", kwargs=next_page_pk)

    if retest_pages[-1] == current_page:
        return reverse("audits:retest-comparison-update", kwargs=retest_pk)

    current_page_position: int = retest_pages.index(current_page)
    next_page_pk: Dict[str, int] = {"pk": retest_pages[current_page_position + 1].id}
    return reverse("audits:edit-retest-page-checks", kwargs=next_page_pk)
