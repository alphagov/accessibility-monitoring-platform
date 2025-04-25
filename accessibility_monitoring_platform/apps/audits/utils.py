"""
Utilities for audits app
"""

from collections import namedtuple
from datetime import date, datetime
from typing import Any, TypeVar

from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.http import Http404, HttpRequest
from django.utils import timezone

from ..common.sitemap import PlatformPage, get_platform_page_by_url_name
from ..common.utils import (
    list_to_dictionary_of_lists,
    record_model_create_event,
    record_model_update_event,
)
from .forms import CheckResultForm
from .models import (
    Audit,
    CheckResult,
    CheckResultRetestNotesHistory,
    Page,
    Retest,
    RetestCheckResult,
    RetestPage,
    RetestStatementCheckResult,
    StatementCheck,
    StatementCheckResult,
    WcagDefinition,
)

MANUAL_CHECK_SUB_TYPE_LABELS: dict[str, str] = {
    "keyboard": "Keyboard",
    "zoom": "Zoom and Reflow",
    "audio-visual": "Audio and Visual",
    "additional": "Additional",
    "other": "Other",
}
StatementContentSubsection = namedtuple(
    "StatementContentSubsection", "name attr_unique url_suffix"
)
STATEMENT_CONTENT_SUBSECTIONS: list[StatementContentSubsection] = [
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

P = TypeVar("P", bound=Page | RetestPage)


def index_or_404(items: list[P], item: P) -> int:
    """Return index of item in list or raise 404 if not found"""
    try:
        position: int = items.index(item)
    except ValueError:
        raise Http404
    return position


def create_or_update_check_results_for_page(
    user: User, page: Page, check_result_forms: list[CheckResultForm]
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
    page: Page, wcag_definitions: list[WcagDefinition]
) -> list[dict[str, str | WcagDefinition]]:
    """
    Combine existing check result with all the WCAG definitions
    to create a list of dictionaries for use in populating the
    CheckResultFormset with all possible results.
    """
    check_results_by_wcag_definition: dict[WcagDefinition, CheckResult] = (
        page.check_results_by_wcag_definition
    )
    check_results: list[dict[str, str | WcagDefinition]] = []

    for wcag_definition in wcag_definitions:
        if wcag_definition in check_results_by_wcag_definition:
            check_result: CheckResult = check_results_by_wcag_definition[
                wcag_definition
            ]
            check_result_state: str = check_result.check_result_state
            notes: str = check_result.notes
            issue_identifier: str = check_result.issue_identifier
        else:
            check_result_state: str = CheckResult.Result.NOT_TESTED
            notes: str = ""
            issue_identifier: str = ""
        check_results.append(
            {
                "wcag_definition": wcag_definition,
                "check_result_state": check_result_state,
                "notes": notes,
                "issue_identifier": issue_identifier,
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


def get_next_platform_page_initial(
    audit: Audit, current_page: Page | None = None
) -> PlatformPage:
    """
    Return the platform page to go to when a save and continue button is
    pressed on the page where pages or page check results are entered.
    """
    if not audit.testable_pages:
        return get_platform_page_by_url_name(
            url_name="audits:edit-website-decision", instance=audit
        )

    if current_page is None:
        return get_platform_page_by_url_name(
            url_name="audits:edit-audit-page-checks",
            instance=audit.testable_pages.first(),
        )

    testable_pages: list[Page] = list(audit.testable_pages)
    if testable_pages[-1] == current_page:
        return get_platform_page_by_url_name(
            url_name="audits:edit-website-decision", instance=audit
        )

    current_page_position: int = index_or_404(items=testable_pages, item=current_page)
    next_page: Page = testable_pages[current_page_position + 1]
    return get_platform_page_by_url_name(
        url_name="audits:edit-audit-page-checks", instance=next_page
    )


def get_next_platform_page_twelve_week(
    audit: Audit, current_page: Page | None = None
) -> PlatformPage:
    """
    Return the platform page page to go to when a save and continue button is
    pressed on the page where pages or page check results are retested.
    """
    testable_pages_with_errors: list[Page] = [
        page for page in audit.testable_pages if page.failed_check_results
    ]
    if not testable_pages_with_errors:
        return get_platform_page_by_url_name(
            url_name="audits:edit-audit-retest-website-decision", instance=audit
        )

    if current_page is None:
        return get_platform_page_by_url_name(
            url_name="audits:edit-audit-retest-page-checks",
            instance=testable_pages_with_errors[0],
        )

    if testable_pages_with_errors[-1] == current_page:
        return get_platform_page_by_url_name(
            url_name="audits:edit-audit-retest-website-decision", instance=audit
        )

    current_page_position: int = index_or_404(
        items=testable_pages_with_errors, item=current_page
    )
    next_page: Page = testable_pages_with_errors[current_page_position + 1]
    return get_platform_page_by_url_name(
        url_name="audits:edit-audit-retest-page-checks", instance=next_page
    )


def other_page_failed_check_results(
    page: Page,
) -> dict[WcagDefinition, list[CheckResult]]:
    """
    Find all failed check results for other pages.
    Return them in a dictionary keyed by their WcagDefinitions.

    Args:
        page (Page): Page object

    Returns:
        dict[WcagDefinition, list[CheckResult]]: Dictionary of failed check results
    """
    failed_check_results_by_wcag_definition: dict[WcagDefinition, list[CheckResult]] = (
        {}
    )
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

    today: date = date.today()
    id_within_case: int = 0
    for statement_check in StatementCheck.objects.on_date(today):
        id_within_case += 1
        RetestStatementCheckResult.objects.create(
            retest=retest,
            statement_check=statement_check,
            type=statement_check.type,
            id_within_case=id_within_case,
        )


def get_next_platform_page_equality_body(
    retest: Retest, current_page: RetestPage | None = None
) -> PlatformPage:
    """
    Return the next retest platform page to go to when a save and continue button is
    pressed.
    """
    retest_pages: list[RetestPage] = list(retest.retestpage_set.all())
    if not retest_pages:
        return get_platform_page_by_url_name(
            url_name="audits:retest-comparison-update", instance=retest
        )

    if current_page is None:
        return get_platform_page_by_url_name(
            url_name="audits:edit-retest-page-checks", instance=retest_pages[0]
        )

    if retest_pages[-1] == current_page:
        return get_platform_page_by_url_name(
            url_name="audits:retest-comparison-update", instance=retest
        )

    current_page_position: int = index_or_404(items=retest_pages, item=current_page)
    next_retest_page: RetestPage = retest_pages[current_page_position + 1]
    return get_platform_page_by_url_name(
        url_name="audits:edit-retest-page-checks", instance=next_retest_page
    )


def get_other_pages_with_retest_notes(page: Page) -> list[Page]:
    """Check other pages of this case for retest notes and return them"""
    audit: Audit = page.audit
    return [
        other_page
        for other_page in audit.testable_pages
        if other_page.retest_notes and other_page != page
    ]


def get_audit_summary_context(request: HttpRequest, audit: Audit) -> dict[str, Any]:
    """Return the context for test summary pages"""
    context: dict[str, Any] = {}
    show_failures_by_page: bool = "page-view" in request.GET
    show_all: bool = "show-all" in request.GET
    context["show_failures_by_page"] = show_failures_by_page
    context["show_all"] = show_all
    context["enable_12_week_ui"] = audit.retest_date is not None

    check_results: QuerySet[CheckResult] = (
        audit.failed_check_results if show_all else audit.unfixed_check_results
    )

    context["audit_failures_by_page"] = list_to_dictionary_of_lists(
        items=check_results, group_by_attr="page"
    )
    context["pages_with_retest_notes"] = audit.testable_pages.exclude(retest_notes="")
    context["audit_failures_by_wcag"] = list_to_dictionary_of_lists(
        items=check_results, group_by_attr="wcag_definition"
    )

    statement_check_results: QuerySet[StatementCheckResult] = (
        audit.statement_check_results
        if show_all
        else audit.outstanding_statement_check_results
    )
    if not audit.all_overview_statement_checks_have_passed:
        statement_check_results = statement_check_results.filter(
            type=StatementCheck.Type.OVERVIEW
        )
    context["statement_check_results_by_type"] = list_to_dictionary_of_lists(
        items=statement_check_results, group_by_attr="type"
    )

    context["number_of_wcag_issues"] = check_results.count()
    context["number_of_statement_issues"] = statement_check_results.count()

    return context


def add_to_check_result_restest_notes_history(
    check_result: CheckResult, request: HttpRequest
) -> None:
    """Add latest chenge to CheckResult.retest_notes history"""
    previous_check_result: CheckResult = CheckResult.objects.get(id=check_result.id)
    if check_result.retest_notes != previous_check_result.retest_notes:
        CheckResultRetestNotesHistory.objects.create(
            check_result=check_result,
            created_by=request.user,
            retest_notes=check_result.retest_notes,
            retest_state=check_result.retest_state,
        )
