"""
Utilities for audits app
"""

from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypeVar

from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.http import Http404, HttpRequest
from django.utils import timezone

from ..common.sitemap import PlatformPage, get_platform_page_by_url_name
from ..common.utils import list_to_dictionary_of_lists
from ..simplified.models import SimplifiedCase
from ..simplified.utils import (
    record_simplified_model_create_event,
    record_simplified_model_update_event,
)
from .forms import WcagCheckResultInitialForm
from .models import (
    AuditOverview,
    CheckResult,
    Page,
    RetestPage,
    StatementAudit,
    StatementCheck,
    StatementCheckResult,
    StatementCheckResultRound,
    WcagAudit,
    WcagCheckResultInitial,
    WcagCheckResultInitialNotesHistory,
    WcagCheckResultRetest,
    WcagCheckResultRetestNotesHistory,
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


def create_or_update_wcag_check_result_initials_for_page(
    user: User,
    wcag_page_initial: WcagPageInitial,
    check_result_forms: list[WcagCheckResultInitialForm],
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
                update_published_report_data_updated_time(
                    wcag_audit=wcag_check_result_initial.wcag_audit
                )
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
            update_published_report_data_updated_time(
                wcag_audit=wcag_page_initial.wcag_audit
            )


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


def create_statement_checks_for_new_audit(statement_audit: StatementAudit) -> None:
    """
    Create statement check results for new audit.
    """
    for statement_check in StatementCheck.objects.on_date(statement_audit.date_of_test):
        StatementCheckResultRound.objects.create(
            statement_audit=statement_audit,
            type=statement_check.type,
            statement_check=statement_check,
        )


def create_retest_wcag_audit_and_check_results(
    audit_overview: AuditOverview, audit_round_type: WcagAudit.AuditRoundType
) -> WcagAudit:

    new_wcag_audit: WcagAudit = WcagAudit.objects.create(
        simplified_case=audit_overview.simplified_case,
        audit_round_type=audit_round_type,
    )
    previous_wcag_audit: WcagAudit = WcagAudit.objects.get(
        simplified_case=audit_overview.simplified_case,
        round_number=new_wcag_audit.round_number - 1,
    )
    if previous_wcag_audit == audit_overview.wcag_audit_initial:
        for wcag_page_initial in previous_wcag_audit.testable_wcag_page_initials:
            wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.create(
                wcag_audit=new_wcag_audit,
                wcag_page_initial=wcag_page_initial,
            )
            for (
                wcag_check_result_initial
            ) in wcag_page_initial.failed_wcag_check_result_initials:
                WcagCheckResultRetest.objects.create(
                    wcag_audit=new_wcag_audit,
                    wcag_page_retest=wcag_page_retest,
                    wcag_check_result_initial=wcag_check_result_initial,
                    wcag_definition=wcag_check_result_initial.wcag_definition,
                )
        else:
            for wcag_page_retest in previous_wcag_audit.retestable_wcag_page_retests:
                wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.create(
                    wcag_audit=new_wcag_audit,
                    wcag_page_initial=wcag_page_retest.wcag_page_initial,
                )
                for (
                    wcag_check_result_retest
                ) in wcag_page_retest.failed_wcag_check_result_retests:
                    WcagCheckResultRetest.objects.create(
                        wcag_audit=new_wcag_audit,
                        wcag_page_retest=wcag_page_retest,
                        wcag_check_result_initial=wcag_check_result_retest.wcag_check_result_initial,
                        wcag_definition=wcag_check_result_retest.wcag_definition,
                    )
    return new_wcag_audit


def create_statement_audit_and_check_results(
    audit_overview: AuditOverview,
    audit_round_type: StatementAudit.AuditRoundType = StatementAudit.AuditRoundType.INITIAL,
) -> StatementAudit:

    if audit_overview.statement_audit_initial is None:
        statement_audit_initial: StatementAudit = StatementAudit.objects.create(
            simplified_case=audit_overview.simplified_case,
        )
        create_statement_checks_for_new_audit(statement_audit=statement_audit_initial)
        return statement_audit_initial
    else:
        statement_audit_initial: StatementAudit = audit_overview.statement_audit_initial
    statement_audit: StatementAudit = StatementAudit.objects.create(
        simplified_case=audit_overview.simplified_case,
        audit_round_type=audit_round_type,
    )
    for (
        statement_check_result_initial
    ) in statement_audit_initial.statement_check_results.exclude(type=None):
        StatementCheckResultRound.objects.create(
            statement_audit=statement_audit,
            statement_check_result_initial=statement_check_result_initial,
            issue_identifier=statement_check_result_initial.issue_identifier,
            statement_check=statement_check_result_initial.statement_check,
            type=statement_check_result_initial.type,
        )
    return statement_audit


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
    wcag_audit: WcagAudit, current_page: WcagPageRetest | None = None
) -> PlatformPage:
    """
    Return the platform page page to go to when a save and continue button is
    pressed on the page where pages or page check results are retested.
    """
    if wcag_audit.wcag_page_retests.count() == 0:
        return get_platform_page_by_url_name(
            url_name="audits:edit-audit-retest-website-decision", instance=wcag_audit
        )

    if current_page is None:
        return get_platform_page_by_url_name(
            url_name="audits:edit-wcag-page-retest-check-results",
            instance=wcag_audit.wcag_page_retests.first(),
        )

    if wcag_audit.wcag_page_retests.last() == current_page:
        return get_platform_page_by_url_name(
            url_name="audits:edit-audit-retest-website-decision", instance=wcag_audit
        )

    wcag_page_retests: list[WcagPageRetest] = list(wcag_audit.wcag_page_retests)
    current_page_position: int = index_or_404(
        items=wcag_page_retests, item=current_page
    )
    next_page: WcagPageRetest = wcag_page_retests[current_page_position + 1]
    return get_platform_page_by_url_name(
        url_name="audits:edit-wcag-page-retest-check-results", instance=next_page
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


def update_published_report_data_updated_time(wcag_audit: WcagAudit) -> None:
    """Record when an update changing report content as occurred."""
    now: datetime = timezone.now()
    audit_overview: AuditOverview = wcag_audit.simplified_case.audit_overview
    audit_overview.published_report_data_updated_time = now
    audit_overview.save()


def create_checkresults_for_wcag_audit_retest(wcag_audit: WcagAudit) -> None:
    """
    Create pages and checkresults for restest from outstanding issues of previous test.
    """

    previous_wcag_audit: WcagAudit = WcagAudit.objects.get(
        simplified_case=wcag_audit.simplified_case,
        round_number=wcag_audit.round_number - 1,
    )

    if previous_wcag_audit.audit_round_type == WcagAudit.AuditRoundType.TWELVE_WEEK:
        for previous_wcag_page_retest in previous_wcag_audit.wcag_page_retests:
            wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.create(
                wcag_audit=wcag_audit,
                wcag_page_initial=previous_wcag_page_retest.wcag_page_initial,
                page_missing_date=previous_wcag_page_retest.page_missing_date,
            )
            for (
                previous_wcag_check_result_retest
            ) in previous_wcag_page_retest.unfixed_wcag_check_result_retests:
                WcagCheckResultRetest.objects.create(
                    wcag_audit=wcag_audit,
                    wcag_page_retest=wcag_page_retest,
                    wcag_check_result_initial=previous_wcag_check_result_retest.wcag_check_result_initial,
                    wcag_definition=previous_wcag_check_result_retest.wcag_definition,
                )
    else:
        for wcag_page_initial in previous_wcag_audit.every_wcag_page_initials:
            wcag_page_retest: WcagPageRetest = WcagPageRetest.objects.create(
                wcag_audit=wcag_audit,
                wcag_page_initial=wcag_page_initial,
            )
            for (
                failed_wcag_check_result_initial
            ) in wcag_page_initial.failed_wcag_check_result_initials:
                WcagCheckResultRetest.objects.create(
                    wcag_audit=wcag_audit,
                    wcag_page_retest=wcag_page_retest,
                    wcag_check_result_initial=failed_wcag_check_result_initial,
                    wcag_definition=failed_wcag_check_result_initial.wcag_definition,
                )


def get_next_platform_page_equality_body(
    wcag_audit: WcagAudit, current_page: WcagPageRetest | None = None
) -> PlatformPage:
    """
    Return the next retest platform page to go to when a save and continue button is
    pressed.
    """
    wcag_page_retests: list[WcagPageRetest] = list(wcag_audit.wcag_page_retests)
    if not wcag_page_retests:
        return get_platform_page_by_url_name(
            url_name="audits:retest-comparison-update", instance=wcag_audit
        )

    if current_page is None:
        return get_platform_page_by_url_name(
            url_name="audits:edit-retest-page-checks", instance=wcag_page_retests[0]
        )

    if wcag_page_retests[-1] == current_page:
        return get_platform_page_by_url_name(
            url_name="audits:retest-comparison-update", instance=wcag_audit
        )

    current_page_position: int = index_or_404(
        items=wcag_page_retests, item=current_page
    )
    next_wcag_page_retest: WcagPageRetest = wcag_page_retests[current_page_position + 1]
    return get_platform_page_by_url_name(
        url_name="audits:edit-retest-page-checks", instance=next_wcag_page_retest
    )


def get_other_pages_with_retest_notes(
    wcag_page_retest: WcagPageRetest,
) -> list[WcagPageRetest]:
    """Check other pages of this case for retest notes and return them"""
    wcag_audit: WcagAudit = wcag_page_retest.wcag_audit
    return [
        other_page
        for other_page in wcag_audit.retestable_wcag_page_retests
        if other_page.notes and other_page != wcag_page_retest
    ]


def get_audit_summary_context(
    request: HttpRequest,
    simplified_case: SimplifiedCase,
) -> dict[str, Any]:
    """Return the context for test summary pages"""
    audit_overview: AuditOverview = simplified_case.audit_overview
    wcag_audit_initial: WcagAudit | None = audit_overview.wcag_audit_initial
    wcag_audit_12_week: WcagAudit | None = (
        audit_overview.first_wcag_audit_12_week_retest
    )
    statement_audit_initial: StatementAudit | None = (
        audit_overview.statement_audit_initial
    )
    statement_audit_12_week: StatementAudit | None = (
        audit_overview.first_statement_audit_12_week_retest
    )
    context: dict[str, Any] = {}
    show_failures_by_page: bool = "page-view" in request.GET
    show_all: bool = "show-all" in request.GET
    context["show_failures_by_page"] = show_failures_by_page
    context["show_all"] = show_all
    context["enable_12_week_ui"] = wcag_audit_12_week is not None
    context["wcag_audit_initial"] = wcag_audit_initial
    context["wcag_audit_12_week"] = wcag_audit_12_week
    context["statement_audit_initial"] = statement_audit_initial
    context["statement_audit_12_week"] = statement_audit_12_week
    if statement_audit_12_week is not None:
        context["statement_audit"] = statement_audit_12_week
    else:
        context["statement_audit"] = statement_audit_initial

    summary_wcag_check_results: list[SummaryWcagCheckResult] = []

    if wcag_audit_initial is not None:
        for (
            wcag_failed_check_result_initial
        ) in wcag_audit_initial.wcag_failed_check_result_initials:
            summary_wcag_check_result: SummaryWcagCheckResult = SummaryWcagCheckResult(
                wcag_definition=wcag_failed_check_result_initial.wcag_definition,
                wcag_page_initial=wcag_failed_check_result_initial.wcag_page_initial,
                issue_identifier=wcag_failed_check_result_initial.issue_identifier,
                initial_result=wcag_failed_check_result_initial,
                retest_result=wcag_failed_check_result_initial.twelve_week_retest,
            )
            if (
                show_all
                or summary_wcag_check_result.retest_result is None
                or summary_wcag_check_result.retest_result.retest_state
                != WcagCheckResultRetest.RetestResult.FIXED
            ):
                summary_wcag_check_results.append(summary_wcag_check_result)

        context["summary_wcag_check_results_by_page"] = list_to_dictionary_of_lists(
            items=summary_wcag_check_results, group_by_attr="wcag_page_initial"
        )

        if wcag_audit_12_week is not None:
            context["pages_with_retest_notes"] = WcagPageRetest.objects.filter(
                wcag_audit=wcag_audit_12_week
            ).exclude(notes="")

        summary_wcag_check_results_by_wcag: dict[WcagDefinition, list[CheckResult]] = (
            list_to_dictionary_of_lists(
                items=summary_wcag_check_results, group_by_attr="wcag_definition"
            )
        )
        for wcag_definition, failures in summary_wcag_check_results_by_wcag.items():
            wcag_definition.issue_identifiers = " ".join(
                [failure.issue_identifier for failure in failures]
            )
        context["summary_wcag_check_results_by_wcag"] = (
            summary_wcag_check_results_by_wcag
        )

    summary_statement_check_results: list[SummaryStatementCheckResult] = []

    statement_check_results: (
        QuerySet[StatementCheckResultRound] | QuerySet[StatementCheckResultRound]
    ) = (
        statement_audit_12_week.statement_check_results
        if statement_audit_12_week is not None
        else statement_audit_initial.statement_check_results
    )

    for statement_check_result in statement_check_results:
        if statement_check_result.statement_check_result_initial is not None:
            initial_result: StatementCheckResultRound = (
                statement_check_result.statement_check_result_initial
            )
            retest_result: StatementCheckResultRound = statement_check_result
        else:
            initial_result: StatementCheckResultRound = statement_check_result
            retest_result: StatementCheckResultRound = (
                statement_check_result.twelve_week_retest
            )

        type: CheckResult.Type = (
            initial_result.type if initial_result is not None else retest_result.type
        )

        summary_statement_check_result: SummaryStatementCheckResult = (
            SummaryStatementCheckResult(
                type=type,
                issue_identifier=statement_check_result.issue_identifier,
                initial_result=initial_result,
                retest_result=retest_result,
            )
        )
        if (
            show_all
            or (
                summary_statement_check_result.initial_result is not None
                and summary_statement_check_result.initial_result.check_result_state
                == StatementCheckResult.Result.NO
            )
            or (
                summary_statement_check_result.retest_result is not None
                and summary_statement_check_result.retest_result.check_result_state
                == StatementCheckResult.Result.NO
            )
        ):
            summary_statement_check_results.append(summary_statement_check_result)

    if statement_audit_initial.all_overview_statement_checks_have_passed or (
        statement_audit_12_week is not None
        and statement_audit_12_week.all_overview_statement_checks_have_passed
    ):
        pass
    else:
        summary_statement_check_results = [
            statement_check_result
            for statement_check_result in summary_statement_check_results
            if statement_check_result.type == StatementCheck.Type.OVERVIEW
        ]

    context["summary_statement_check_results"] = summary_statement_check_results
    context["summary_statement_check_results_by_type"] = list_to_dictionary_of_lists(
        items=summary_statement_check_results, group_by_attr="type"
    )

    context["number_of_wcag_issues"] = len(summary_wcag_check_results)
    context["number_of_statement_issues"] = len(summary_statement_check_results)

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
    wcag_check_result_retest: WcagCheckResultRetest,
    user: User,
    new_check_result_retest: bool = False,
) -> None:
    """Add latest change to WcagCheckResultRetest.notes history"""
    if new_check_result_retest is True:
        previous_wcag_check_result_retest: None = None
    else:
        previous_wcag_check_result_retest: WcagCheckResultRetest | None = (
            WcagCheckResultRetest.objects.filter(id=wcag_check_result_retest.id).first()
            if wcag_check_result_retest.id is not None
            else None
        )
    if (
        previous_wcag_check_result_retest is None
        or wcag_check_result_retest.notes != previous_wcag_check_result_retest.notes
    ):
        if wcag_check_result_retest.notes:
            WcagCheckResultRetestNotesHistory.objects.create(
                wcag_check_result_retest=wcag_check_result_retest,
                created_by=user,
                retest_state=wcag_check_result_retest.retest_state,
                notes=wcag_check_result_retest.notes,
            )


def build_equality_body_retest_context_data(
    wcag_audit: WcagAudit | None = None, statement_audit: StatementAudit | None = None
) -> dict[str, Any]:
    """Populate context data for equality body retest template rendering"""
    context: dict[str, Any] = {}

    if wcag_audit is not None:
        statement_audit: StatementAudit = (
            wcag_audit.equivalent_equality_body_statement_retest
        )
    else:
        wcag_audit: WcagAudit = statement_audit.equivalent_equality_body_wcag_retest

    audit_overview: AuditOverview = statement_audit.simplified_case.audit_overview

    context["wcag_audit_initial"] = audit_overview.wcag_audit_initial
    context["first_wcag_audit_12_week_retest"] = (
        audit_overview.first_wcag_audit_12_week_retest
    )
    context["statement_audit"] = statement_audit
    context["wcag_audit"] = wcag_audit

    return context
