"""Build context for email template rendering"""

from datetime import date, timedelta
from typing import Any

from ..reports.utils import build_issues_tables
from ..simplified.models import SimplifiedCase

SESSION_EXPIRY_WARNING_WINDOW: timedelta = timedelta(hours=12)
ONE_WEEK_IN_DAYS: int = 7
TWELVE_WEEKS_IN_DAYS: int = 12 * ONE_WEEK_IN_DAYS


def get_email_template_context(simplified_case: SimplifiedCase) -> dict[str, Any]:
    context: dict[str, Any] = {}
    context["12_weeks_from_today"] = date.today() + timedelta(days=TWELVE_WEEKS_IN_DAYS)
    context["case"] = simplified_case
    context["retest"] = simplified_case.retests.first()
    if simplified_case.audit is not None:
        context["issues_tables"] = build_issues_tables(
            pages=simplified_case.audit.testable_pages,
            check_results_attr="unfixed_check_results",
        )
        context["retest_issues_tables"] = build_issues_tables(
            pages=simplified_case.audit.retestable_pages,
            use_retest_notes=True,
            check_results_attr="unfixed_check_results",
        )
    return context
