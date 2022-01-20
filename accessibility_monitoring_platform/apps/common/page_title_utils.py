""" Derive page title from url path """
import re

from ..cases.models import Case

PAGE_TITLES_BY_URL = {
    "/": "Dashboard",
    "/accounts/login/": "Sign in",
    "/accounts/password_reset/": "Reset password",
    "/accounts/password_reset/done/": "Password reset done",
    "/cases/": "Search",
    "/cases/[id]/delete-case/": "Delete case",
    "/cases/[id]/edit-case-details/": "Case details",
    "/cases/[id]/edit-contact-details/": "Contact details",
    "/cases/[id]/edit-enforcement-body-correspondence/": "Equality body correspondence",
    "/cases/[id]/edit-final-decision/": "Final decision",
    "/cases/[id]/edit-no-psb-response/": "Public sector body is unresponsive",
    "/cases/[id]/edit-report-correspondence/": "Report correspondence",
    "/cases/[id]/edit-report-details/": "Report details",
    "/cases/[id]/edit-qa-process/": "QA process",
    "/cases/[id]/edit-report-followup-due-dates/": "Report followup dates",
    "/cases/[id]/edit-test-results/": "Testing details",
    "/cases/[id]/edit-twelve-week-correspondence-due-dates/": "12 week correspondence dates",
    "/cases/[id]/edit-twelve-week-correspondence/": "12 week correspondence",
    "/cases/[id]/view/": "View case",
    "/cases/create/": "Create case",
    "/contact/": "Contact admin",
    "/notifications/notifications-list/": "Notifications",
    "/reminders/cases/[id]/reminder-create/": "Reminder",
    "/reminders/reminder-list/": "Reminders",
    "/report-issue/": "Report an issue",
    "/user/account_details/": "Account details",
    "/user/register/": "Register",
    "/websites/": "Query domain register",
}


def get_page_title(path: str) -> str:
    """Derive page title from path"""
    path_without_id = re.sub(r"\d+", "[id]", path)
    page_heading: str = PAGE_TITLES_BY_URL.get(
        path_without_id, "Accessibility Monitoring Platform"
    )

    page_title: str = page_heading
    if path_without_id.startswith("/cases/[id]/"):
        try:
            case: Case = Case.objects.get(id=path.split("/")[2])
            page_title: str = f"{case.organisation_name} | {page_heading}"
        except Case.DoesNotExist:
            pass
    elif path_without_id == "/reminders/cases/[id]/reminder-create/":
        try:
            case: Case = Case.objects.get(id=path.split("/")[3])
            page_title: str = f"{case.organisation_name} | {page_heading}"
        except Case.DoesNotExist:
            pass
    return page_title
