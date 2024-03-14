"""
Utilities for audits app
"""

from collections import namedtuple
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
from ..common.view_section_utils import ViewSection, ViewSubTable, build_view_section
from .forms import (
    ArchiveAuditReportOptionsUpdateForm,
    ArchiveAuditStatement1UpdateForm,
    ArchiveAuditStatement2UpdateForm,
    AuditMetadataUpdateForm,
    CaseComplianceStatement12WeekUpdateForm,
    CaseComplianceStatementInitialUpdateForm,
    CaseComplianceWebsite12WeekUpdateForm,
    CaseComplianceWebsiteInitialUpdateForm,
    CheckResultForm,
    InitialDisproportionateBurdenUpdateForm,
    TwelveWeekDisproportionateBurdenUpdateForm,
)
from .models import (
    ARCHIVE_REPORT_ACCESSIBILITY_ISSUE_TEXT,
    ARCHIVE_REPORT_NEXT_ISSUE_TEXT,
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
StatementContentSubsection = namedtuple(
    "StatementContentSubsection", "name attr_unique url_suffix"
)
STATEMENT_CONTENT_SUBSECTIONS: List[StatementContentSubsection] = [
    StatementContentSubsection("Statement information", "website", "website"),
    StatementContentSubsection("Compliance status", "compliance", "compliance"),
    StatementContentSubsection(
        "Non-accessible content", "non_accessible", "non-accessible"
    ),
    StatementContentSubsection(
        "Preparation of this accessibility statement", "preparation", "preparation"
    ),
    StatementContentSubsection(
        "Feedback and enforcement procedure", "feedback", "feedback"
    ),
    StatementContentSubsection("Custom statement issues", "custom", "custom"),
]


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


def get_test_view_tables_context(audit: Audit):
    get_audit_rows: Callable = partial(extract_form_labels_and_values, instance=audit)
    get_compliance_rows: Callable = partial(
        extract_form_labels_and_values, instance=audit.case.compliance
    )
    return {
        "audit_metadata_rows": get_audit_rows(form=AuditMetadataUpdateForm()),
        "website_decision_rows": get_compliance_rows(
            form=CaseComplianceWebsiteInitialUpdateForm()
        ),
        "initial_disproportionate_burden": get_audit_rows(
            form=InitialDisproportionateBurdenUpdateForm()
        ),
        "audit_statement_1_rows": get_audit_rows(
            form=ArchiveAuditStatement1UpdateForm()
        ),
        "audit_statement_2_rows": get_audit_rows(
            form=ArchiveAuditStatement2UpdateForm()
        ),
        "statement_decision_rows": get_compliance_rows(
            form=CaseComplianceStatementInitialUpdateForm()
        ),
        "audit_report_options_rows": get_audit_report_options_rows(audit=audit),
    }


def build_statement_content_subsections(audit: Audit) -> List[ViewSection]:
    """
    Build view sections for each type of statement content check.
    """
    return [
        build_view_section(
            name=statement_content_subsection.name,
            edit_url=reverse(
                f"audits:edit-statement-{statement_content_subsection.url_suffix}",
                kwargs={"pk": audit.id},
            ),
            edit_url_id=f"edit-statement-{statement_content_subsection.url_suffix}",
            complete_date=getattr(
                audit,
                f"audit_statement_{statement_content_subsection.attr_unique}_complete_date",
            ),
            display_fields=[
                FieldLabelAndValue(
                    label=statement_check_result.label,
                    value=statement_check_result.display_value,
                )
                for statement_check_result in getattr(
                    audit,
                    f"{statement_content_subsection.attr_unique}_statement_check_results",
                )
            ],
        )
        for statement_content_subsection in STATEMENT_CONTENT_SUBSECTIONS
    ]


def get_test_view_sections(audit: Audit) -> List[ViewSection]:
    """Get sections for latest test view"""
    get_audit_rows: Callable = partial(extract_form_labels_and_values, instance=audit)
    get_compliance_rows: Callable = partial(
        extract_form_labels_and_values, instance=audit.case.compliance
    )
    audit_pk: Dict[str, int] = {"pk": audit.id}
    pre_statement_check_sections: List[ViewSection] = [
        build_view_section(
            name="Test metadata",
            edit_url=reverse("audits:edit-audit-metadata", kwargs=audit_pk),
            edit_url_id="edit-audit-metadata",
            complete_date=audit.audit_metadata_complete_date,
            display_fields=get_audit_rows(form=AuditMetadataUpdateForm()),
        ),
        build_view_section(
            name="Pages",
            edit_url=reverse("audits:edit-audit-pages", kwargs=audit_pk),
            edit_url_id="edit-audit-pages",
            complete_date=audit.audit_pages_complete_date,
            display_fields=[
                FieldLabelAndValue(
                    type=FieldLabelAndValue.URL_TYPE,
                    label=str(page),
                    value=page.url,
                )
                for page in audit.testable_pages
            ],
            subsections=[
                build_view_section(
                    name=f"{str(page)} ({page.failed_check_results.count()})",
                    edit_url=reverse(
                        "audits:edit-audit-page-checks", kwargs={"pk": page.id}
                    ),
                    edit_url_id=f"page-{page.id}",
                    complete_date=page.complete_date,
                    display_fields=[
                        FieldLabelAndValue(
                            type=FieldLabelAndValue.NOTES_TYPE,
                            label=check_result.wcag_definition,
                            value=check_result.notes,
                        )
                        for check_result in page.failed_check_results
                    ],
                )
                for page in audit.testable_pages
            ],
        ),
        build_view_section(
            name="Website compliance decision",
            edit_url=reverse("audits:edit-website-decision", kwargs=audit_pk),
            edit_url_id="edit-website-decision",
            complete_date=audit.audit_website_decision_complete_date,
            display_fields=get_compliance_rows(
                form=CaseComplianceWebsiteInitialUpdateForm()
            ),
        ),
        build_view_section(
            name="Statement links",
            edit_url=reverse("audits:edit-statement-pages", kwargs=audit_pk),
            edit_url_id="edit-statement-pages",
            complete_date=audit.audit_statement_pages_complete_date,
            subtables=[
                ViewSubTable(
                    name=f"Statement {count}",
                    display_fields=[
                        FieldLabelAndValue(
                            type=FieldLabelAndValue.URL_TYPE,
                            label="Link to statement",
                            value=statement_page.url,
                        ),
                        FieldLabelAndValue(
                            type=FieldLabelAndValue.URL_TYPE,
                            label="Statement backup",
                            value=statement_page.backup_url,
                        ),
                        FieldLabelAndValue(
                            label="Statement added",
                            value=statement_page.get_added_stage_display(),
                        ),
                        FieldLabelAndValue(
                            type=FieldLabelAndValue.DATE_TYPE,
                            label="Created",
                            value=statement_page.created,
                        ),
                    ],
                )
                for count, statement_page in enumerate(audit.statement_pages, start=1)
            ],
        ),
    ]
    if audit.uses_statement_checks:
        statement_content_subsections: List[ViewSection] = (
            build_statement_content_subsections(audit=audit)
            if audit.all_overview_statement_checks_have_passed
            else []
        )
        statement_content_sections: List[ViewSection] = [
            build_view_section(
                name="Statement overview",
                edit_url=reverse("audits:edit-statement-overview", kwargs=audit_pk),
                edit_url_id="edit-statement-overview",
                complete_date=audit.audit_statement_overview_complete_date,
                display_fields=[
                    FieldLabelAndValue(
                        label=statement_check_result.label,
                        value=statement_check_result.display_value,
                    )
                    for statement_check_result in audit.overview_statement_check_results
                ],
                subsections=statement_content_subsections,
            ),
        ]
    else:
        statement_content_sections: List[ViewSection] = [
            build_view_section(
                name="Accessibility statement Pt. 1",
                edit_url=reverse("audits:edit-audit-statement-1", kwargs=audit_pk),
                edit_url_id="edit-audit-statement-1",
                complete_date=audit.archive_audit_statement_1_complete_date,
                display_fields=get_audit_rows(form=ArchiveAuditStatement1UpdateForm()),
            ),
            build_view_section(
                name="Accessibility statement Pt. 2",
                edit_url=reverse("audits:edit-audit-statement-2", kwargs=audit_pk),
                edit_url_id="edit-audit-statement-2",
                complete_date=audit.archive_audit_statement_2_complete_date,
                display_fields=get_audit_rows(form=ArchiveAuditStatement2UpdateForm()),
            ),
            build_view_section(
                name="Report options",
                edit_url=reverse("audits:edit-audit-report-options", kwargs=audit_pk),
                edit_url_id="edit-audit-report-options",
                complete_date=audit.archive_audit_report_options_complete_date,
                display_fields=get_audit_report_options_rows(audit=audit),
            ),
        ]
    post_statement_check_sections: List[ViewSection] = [
        build_view_section(
            name="Initial disproportionate burden claim",
            edit_url=reverse(
                "audits:edit-initial-disproportionate-burden", kwargs=audit_pk
            ),
            edit_url_id="edit-initial-disproportionate-burden",
            complete_date=audit.initial_disproportionate_burden_complete_date,
            display_fields=get_audit_rows(
                form=InitialDisproportionateBurdenUpdateForm()
            ),
        ),
        build_view_section(
            name="Initial statement compliance decision",
            edit_url=reverse("audits:edit-statement-decision", kwargs=audit_pk),
            edit_url_id="edit-statement-decision",
            complete_date=audit.audit_statement_decision_complete_date,
            display_fields=get_compliance_rows(
                form=CaseComplianceStatementInitialUpdateForm()
            ),
        ),
        build_view_section(
            name="Test summary",
            edit_url=reverse("audits:edit-audit-summary", kwargs=audit_pk),
            edit_url_id="edit-audit-summary",
            anchor="",
        ),
    ]
    return (
        pre_statement_check_sections
        + statement_content_sections
        + post_statement_check_sections
    )


def get_retest_view_tables_context(case: Case) -> Dict[str, List[FieldLabelAndValue]]:
    """Get context for 12-week retest view tables"""
    get_audit_rows: Callable = partial(
        extract_form_labels_and_values, instance=case.audit
    )
    get_compliance_rows: Callable = partial(
        extract_form_labels_and_values, instance=case.compliance
    )
    return {
        "audit_retest_website_decision_rows": get_compliance_rows(
            form=CaseComplianceWebsite12WeekUpdateForm()
        ),
        "twelve_week_disproportionate_burden": get_audit_rows(
            form=TwelveWeekDisproportionateBurdenUpdateForm()
        ),
        "audit_retest_statement_decision_rows": get_compliance_rows(
            form=CaseComplianceStatement12WeekUpdateForm()
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
        elif notes != "" or check_result_state != CheckResult.Result.NOT_TESTED:
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
            check_result_state: str = CheckResult.Result.NOT_TESTED
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

    for page_type in Page.MANDATORY_PAGE_TYPES:
        if page_type == Page.Type.HOME:
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
        return reverse("audits:edit-audit-retest-pages-comparison", kwargs=audit_pk)

    if current_page is None:
        next_page_pk: Dict[str, int] = {"pk": testable_pages_with_errors[0].id}
        return reverse("audits:edit-audit-retest-page-checks", kwargs=next_page_pk)

    if testable_pages_with_errors[-1] == current_page:
        return reverse("audits:edit-audit-retest-pages-comparison", kwargs=audit_pk)

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
                    retest=retest_0,
                    page=page,
                    additional_issues_notes=page.retest_notes,
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
