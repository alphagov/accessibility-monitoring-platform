"""
Context processors
"""
from datetime import date
import re
from typing import Dict, Union

from ..cases.models import Case
from ..common.models import Platform
from ..common.utils import get_platform_settings
from ..reminders.models import Reminder

from .forms import AMPTopMenuForm


PAGE_TITLES_BY_URL = {
    "/": "Dashboard",
    "/accounts/login/": "Sign in",
    "/accounts/password_reset/": "Reset password",
    "/accounts/password_reset/done/": "Password reset done",
    "/cases/": "Search",
    "/cases/[id]/delete-case/": "Delete case",
    "/cases/[id]/edit-case-details/": "Edit case | Case details",
    "/cases/[id]/edit-contact-details/": "Edit case | Contact details",
    "/cases/[id]/edit-enforcement-body-correspondence/": "Edit case | Equality body correspondence",
    "/cases/[id]/edit-final-decision/": "Edit case | Final decision",
    "/cases/[id]/edit-no-psb-response/": "Edit case | Public sector body is unresponsive",
    "/cases/[id]/edit-report-correspondence/": "Edit case | Report correspondence",
    "/cases/[id]/edit-report-details/": "Edit case | Report details",
    "/cases/[id]/edit-qa-process/": "Edit case | QA process",
    "/cases/[id]/edit-report-followup-due-dates/": "Edit case | Report followup dates",
    "/cases/[id]/edit-test-results/": "Edit case | Testing details",
    "/cases/[id]/edit-twelve-week-correspondence-due-dates/": "Edit case | 12 week correspondence dates",
    "/cases/[id]/edit-twelve-week-correspondence/": "Edit case | 12 week correspondence",
    "/cases/[id]/view/": "View case",
    "/cases/create/": "Create case",
    "/contact/": "Contact admin",
    "/report-issue/": "Report an issue",
    "/user/account_details/": "Account details",
    "/user/register/": "Register",
    "/websites/": "Query domain register",
}


def platform_page(request) -> Dict[str, Union[int, str, AMPTopMenuForm, Platform]]:
    """
    Lookup the page title using URL path and place it in context for template rendering.
    Also include search form for top menu, name of prototype and platform settings.
    """
    url_without_id = re.sub(r"\d+", "[id]", request.path)
    page_heading: str = PAGE_TITLES_BY_URL.get(
        url_without_id, "Accessibility Monitoring Platform"
    )

    page_title: str = page_heading
    if url_without_id.startswith("/cases/[id]/"):
        try:
            case: Case = Case.objects.get(id=request.path.split("/")[2])
            page_title: str = f"{case.organisation_name} | {page_heading}"
        except Case.DoesNotExist:
            pass

    absolute_uri: str = request.build_absolute_uri()
    if (
        "localhost" in absolute_uri
        or "accessibility-monitoring-platform-production.london.cloudapps.digital"
        in absolute_uri
        or "accessibility-monitoring-platform-test.london.cloudapps.digital"
        in absolute_uri
    ):
        prototype_name: str = ""
    else:
        prototype_name: str = (
            absolute_uri.split(".")[0].replace("https://", "").replace("http://", "")
        )

    platform: Platform = get_platform_settings()

    today: date = date.today()
    number_of_reminders: int = Reminder.objects.filter(
        is_deleted=False, user=request.user, due_date__lte=today
    ).count()

    return {
        "page_heading": page_heading,
        "page_title": page_title,
        "top_menu_form": AMPTopMenuForm(),
        "prototype_name": prototype_name,
        "platform": platform,
        "number_of_reminders": number_of_reminders,
    }
