""" Build context for email template rendering """

from datetime import date, timedelta
from typing import Any

from ..cases.models import Case
from ..reports.utils import build_issues_tables

SESSION_EXPIRY_WARNING_WINDOW: timedelta = timedelta(hours=12)
ONE_WEEK_IN_DAYS: int = 7
TWELVE_WEEKS_IN_DAYS: int = 12 * ONE_WEEK_IN_DAYS


def get_email_template_context(case: Case) -> dict[str, Any]:
    context: dict[str, Any] = {}
    context["12_weeks_from_today"] = date.today() + timedelta(days=TWELVE_WEEKS_IN_DAYS)
    context["case"] = case
    context["retest"] = case.retests.first()
    if case.audit is not None:
        context["issues_tables"] = build_issues_tables(
            pages=case.audit.testable_pages,
            check_results_attr="unfixed_check_results",
        )
        context["retest_issues_tables"] = build_issues_tables(
            pages=case.audit.retestable_pages,
            use_retest_notes=True,
            check_results_attr="unfixed_check_results",
        )
    return context
