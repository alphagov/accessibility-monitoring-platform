"""
Utilities for audits app
"""

from collections import namedtuple
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, TypeVar

from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.http import Http404, HttpRequest
from django.utils import timezone

from ..common.sitemap import PlatformPage, get_platform_page_by_url_name
from ..common.utils import list_to_dictionary_of_lists
from ..simplified.utils import (
    record_simplified_model_create_event,
    record_simplified_model_update_event,
)
from .forms import CheckResultForm
from .models import (
    Audit,
    CheckResult,
    Page,
    Retest,
    RetestCheckResult,
    RetestPage,
    RetestStatementCheckResult,
    StatementAudit,
    StatementCheck,
    StatementCheckResult,
    WcagAudit,
    WcagCheckResultInitial,
    WcagCheckResultInitialNotesHistory,
    WcagCheckResultRetest,
    WcagDefinition,
    WcagPageInitial,
    WcagPageRetest,
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


@dataclass
class SummaryWcagCheckResult:
    wcag_definition: WcagDefinition
    wcag_page_initial: WcagPageInitial
    issue_identifier: str
    initial_result: WcagCheckResultInitial
    retest_result: WcagCheckResultRetest | None = None


@dataclass
class SummaryStatementCheckResult:
    type: StatementCheck.Type | None
    issue_identifier: str
    initial_result: StatementCheckResult
    retest_result: StatementCheckResult | None = None


def create_or_update_check_results_for_page(
    user: User,
    wcag_page_initial: WcagPageInitial,
    check_result_forms: list[CheckResultForm],
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
        if (
            wcag_definition
            in wcag_page_initial.wcag_check_result_initials_by_wcag_definition
        ):
            wcag_check_result_initial: WcagCheckResultInitial = (
                wcag_page_initial.wcag_check_result_initials_by_wcag_definition[
                    wcag_definition
                ]
            )
            if (
                wcag_check_result_initial.check_result_state != check_result_state
                or wcag_check_result_initial.notes != notes
            ):
                wcag_check_result_initial.check_result_state = check_result_state
                wcag_check_result_initial.notes = notes
                record_simplified_model_update_event(
                    user=user,
                    model_object=wcag_check_result_initial,
                    simplified_case=wcag_check_result_initial.wcag_audit.simplified_case,
                )
                add_to_check_result_notes_history(
                    wcag_check_result_initial=wcag_check_result_initial, user=user
                )
                report_data_updated(audit=wcag_check_result_initial.audit)
                wcag_check_result_initial.save()
        elif (
            notes != ""
            or check_result_state != WcagCheckResultInitial.Result.NOT_TESTED
        ):
            wcag_check_result_initial: WcagCheckResultInitial = (
                WcagCheckResultInitial.objects.create(
                    wcag_audit=wcag_page_initial.wcag_audit,
                    wcag_page_initial=wcag_page_initial,
                    wcag_definition=wcag_definition,
                    type=wcag_definition.type,
                    check_result_state=check_result_state,
                    notes=notes,
                )
            )
            record_simplified_model_create_event(
                user=user,
                model_object=wcag_check_result_initial,
                simplified_case=wcag_check_result_initial.wcag_audit.simplified_case,
            )
            add_to_check_result_notes_history(
                wcag_check_result_initial=wcag_check_result_initial,
                user=user,
                new_check_result=True,
            )
            report_data_updated(wcag_audit=wcag_page_initial.wcag_audit)


def get_page_check_results_formset_initial(
    wcag_page_initial: WcagPageInitial, wcag_definitions: list[WcagDefinition]
) -> list[dict[str, str | WcagDefinition | CheckResult]]:
    """
    Combine existing check result with all the WCAG definitions
    to create a list of dictionaries for use in populating the
    CheckResultFormset with all possible results.
    """
    check_results_by_wcag_definition: dict[WcagDefinition, WcagCheckResultInitial] = (
        wcag_page_initial.wcag_check_result_initials_by_wcag_definition
    )
    check_results_formset_initial: list[
        dict[str, str | WcagDefinition | CheckResult]
    ] = []

    for wcag_definition in wcag_definitions:
        if wcag_definition in check_results_by_wcag_definition:
            check_result: CheckResult = check_results_by_wcag_definition[
                wcag_definition
            ]
            check_result_state: str = check_result.check_result_state
            notes: str = check_result.notes
            issue_identifier: str = check_result.issue_identifier
        else:
            check_result: None = None
            check_result_state: str = CheckResult.Result.NOT_TESTED
            notes: str = ""
            issue_identifier: str = ""
        check_results_formset_initial.append(
            {
                "wcag_definition": wcag_definition,
                "check_result": check_result,
                "check_result_state": check_result_state,
                "notes": notes,
                "issue_identifier": issue_identifier,
            }
        )
    return check_results_formset_initial


def create_mandatory_pages_for_new_audit(wcag_audit: WcagAudit) -> None:
    """
    Create mandatory pages for new audit.
    """

    for page_type in WcagPageInitial.MANDATORY_PAGE_TYPES:
        if page_type == WcagPageInitial.Type.HOME:
            WcagPageInitial.objects.create(
                wcag_audit=wcag_audit,
                page_type=page_type,
                url=wcag_audit.simplified_case.home_page_url,
            )
        else:
            WcagPageInitial.objects.create(wcag_audit=wcag_audit, page_type=page_type)


def create_statement_checks_for_new_audit(
    audit: Audit, statement_audit: StatementAudit
) -> None:
    """
    Create statement check results for new audit.
    """
    today: date = date.today()
    for statement_check in StatementCheck.objects.on_date(today):
        StatementCheckResult.objects.create(
            audit=audit,
            statement_audit=statement_audit,
            type=statement_check.type,
            statement_check=statement_check,
        )


def get_next_platform_page_wcag_page_initial(
    wcag_audit: WcagAudit, current_wcag_page_initial: WcagPageInitial | None = None
) -> PlatformPage:
    """
    Return the platform page to go to when a save and continue button is
    pressed on the page where pages or page check results are entered.
    """
    if not wcag_audit.testable_wcag_page_initials:
        return get_platform_page_by_url_name(
            url_name="audits:edit-website-decision", instance=wcag_audit
        )

    if current_wcag_page_initial is None:
        return get_platform_page_by_url_name(
            url_name="audits:edit-audit-page-checks",
            instance=wcag_audit.testable_wcag_page_initials.first(),
        )

    testable_pages: list[WcagPageInitial] = list(wcag_audit.testable_wcag_page_initials)
    if testable_pages[-1] == current_wcag_page_initial:
        return get_platform_page_by_url_name(
            url_name="audits:edit-website-decision", instance=wcag_audit
        )

    current_page_position: int = index_or_404(
        items=testable_pages, item=current_wcag_page_initial
    )
    next_page: WcagPageInitial = testable_pages[current_page_position + 1]
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
    wcag_page_initial: WcagPageInitial,
) -> dict[WcagDefinition, list[CheckResult]]:
    """
    Find all failed check results for other pages.
    Return them in a dictionary keyed by their WcagDefinitions.
    """
    failed_check_results_by_wcag_definition: dict[WcagDefinition, list[CheckResult]] = (
        {}
    )
    for (
        check_result
    ) in wcag_page_initial.wcag_audit.wcag_failed_check_result_initials.exclude(
        wcag_page_initial=wcag_page_initial
    ):
        if check_result.wcag_definition in failed_check_results_by_wcag_definition:
            failed_check_results_by_wcag_definition[
                check_result.wcag_definition
            ].append(check_result)
        else:
            failed_check_results_by_wcag_definition[check_result.wcag_definition] = [
                check_result
            ]
    return failed_check_results_by_wcag_definition


def report_data_updated(wcag_audit: WcagAudit) -> None:
    """Record when an update changing report content as occurred."""
    now: datetime = timezone.now()
    audit: Audit = wcag_audit.simplified_case.audit
    audit.published_report_data_updated_time = now
    audit.save()


def create_checkresults_for_retest(retest: Retest) -> None:
    """
    Create pages and checkresults for restest from outstanding issues of previous test.
    """

    audit: Audit = retest.simplified_case.audit
    if retest.id_within_case == 1:
        # Create fake retest from 12-week results for first retest to compare itself to
        retest_0: Retest = Retest.objects.create(
            simplified_case=retest.simplified_case, id_within_case=0
        )
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

    previous_retest: Retest = retest.simplified_case.retests.filter(
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


def get_audit_summary_context(
    request: HttpRequest,
    wcag_audit_initial: WcagAudit | None,
    wcag_audit_12_week: WcagAudit | None,
    statement_audit_initial: StatementAudit | None,
    statement_audit_12_week: StatementAudit | None,
) -> dict[str, Any]:
    """Return the context for test summary pages"""
    context: dict[str, Any] = {}
    show_failures_by_page: bool = "page-view" in request.GET
    show_all: bool = "show-all" in request.GET
    context["show_failures_by_page"] = show_failures_by_page
    context["show_all"] = show_all
    context["enable_12_week_ui"] = wcag_audit_12_week is not None

    wcag_check_results: list[SummaryWcagCheckResult] = []

    if wcag_audit_initial is not None:
        for (
            wcag_failed_check_result_initial
        ) in wcag_audit_initial.wcag_failed_check_result_initials:
            summary_wcag_check_result: SummaryWcagCheckResult = SummaryWcagCheckResult(
                wcag_definition=wcag_failed_check_result_initial.wcag_definition,
                wcag_page_initial=wcag_failed_check_result_initial.wcag_page_initial,
                issue_identifier=wcag_failed_check_result_initial.issue_identifier,
                initial_result=wcag_failed_check_result_initial,
                retest_result=wcag_failed_check_result_initial.last_12_week_retest,
            )
            if (
                show_all
                or summary_wcag_check_result.retest_result is None
                or summary_wcag_check_result.retest_result.retest_state
                != WcagCheckResultRetest.RetestResult.FIXED
            ):
                wcag_check_results.append(summary_wcag_check_result)

        context["audit_failures_by_page"] = list_to_dictionary_of_lists(
            items=wcag_check_results, group_by_attr="wcag_page_initial"
        )

        if wcag_audit_12_week is not None:
            context["pages_with_retest_notes"] = WcagPageRetest.objects.filter(
                wcag_audit=wcag_audit_12_week
            ).exclude(notes="")

        audit_failures_by_wcag: dict[WcagDefinition, list[CheckResult]] = (
            list_to_dictionary_of_lists(
                items=wcag_check_results, group_by_attr="wcag_definition"
            )
        )
        for wcag_definition, failures in audit_failures_by_wcag.items():
            wcag_definition.issue_identifiers = " ".join(
                [failure.issue_identifier for failure in failures]
            )
        context["audit_failures_by_wcag"] = audit_failures_by_wcag

    statement_check_results: list[SummaryStatementCheckResult] = []

    if statement_audit_initial is not None:
        for (
            statement_check_result
        ) in statement_audit_initial.statementcheckresult_set.all():
            type: StatementCheck.Type | None = (
                statement_check_result.statement_check.type
                if statement_check_result.statement_check is not None
                else None
            )
            summary_statement_check_result: SummaryStatementCheckResult = (
                SummaryStatementCheckResult(
                    type=type,
                    issue_identifier=statement_check_result.issue_identifier,
                    initial_result=statement_check_result,
                    retest_result=statement_check_result.twelve_week_retest,
                )
            )
            if (
                show_all
                or summary_statement_check_result.retest_result is None
                or summary_statement_check_result.retest_result.check_result_state
                == StatementCheckResult.Result.NO
            ):
                statement_check_results.append(summary_statement_check_result)

    if (
        statement_audit_initial.all_overview_statement_checks_have_passed
        or statement_audit_12_week.all_overview_statement_checks_have_passed
    ):
        pass
    else:
        statement_check_results = [
            statement_check_result
            for statement_check_result in statement_check_results
            if statement_check_result.type == StatementCheck.Type.OVERVIEW
        ]

    context["statement_check_results"] = statement_check_results
    context["statement_check_results_by_type"] = list_to_dictionary_of_lists(
        items=statement_check_results, group_by_attr="type"
    )

    context["number_of_wcag_issues"] = len(wcag_check_results)
    context["number_of_statement_issues"] = len(statement_check_results)

    return context


def add_to_check_result_notes_history(
    wcag_check_result_initial: WcagCheckResultInitial,
    user: User,
    new_check_result: bool = False,
) -> None:
    """Add latest change to CheckResult.notes history"""
    if new_check_result is True:
        previous_wcag_check_result_initial: None = None
    else:
        previous_wcag_check_result_initial: WcagCheckResultInitial | None = (
            WcagCheckResultInitial.objects.filter(
                id=wcag_check_result_initial.id
            ).first()
            if wcag_check_result_initial.id is not None
            else None
        )
    if (
        previous_wcag_check_result_initial is None
        or wcag_check_result_initial.notes != previous_wcag_check_result_initial.notes
    ):
        WcagCheckResultInitialNotesHistory.objects.create(
            wcag_check_result_initial=wcag_check_result_initial,
            created_by=user,
            notes=wcag_check_result_initial.notes,
        )


def add_to_check_result_restest_notes_history(
    wcag_check_result_initial: WcagCheckResultInitial, user: User
) -> None:
    """Add latest change to CheckResult.retest_notes history"""
    previous_wcag_check_result_initial: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.get(id=wcag_check_result_initial.id)
    )
    if (
        wcag_check_result_initial.retest_notes
        != previous_wcag_check_result_initial.retest_notes
    ):
        WcagCheckResultInitialNotesHistory.objects.create(
            wcag_check_result_initial=wcag_check_result_initial,
            created_by=user,
            retest_notes=wcag_check_result_initial.retest_notes,
            retest_state=wcag_check_result_initial.retest_state,
        )
