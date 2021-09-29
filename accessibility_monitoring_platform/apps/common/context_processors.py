"""
Context processors
"""
import re
from typing import Dict

from ..cases.forms import TopMenuSearchForm
from ..cases.models import Case

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


def platform_page(request) -> Dict[str, str]:
    """
    Lookup the page title using URL path and place it in context for template rendering.
    Also include search form for top menu.
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

    return {
        "page_heading": page_heading,
        "page_title": page_title,
        "nav_bar_form": TopMenuSearchForm(),
    }
