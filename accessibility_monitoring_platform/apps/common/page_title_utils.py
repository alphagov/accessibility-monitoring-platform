""" Derive page title from url path """
import re

from ..audits.models import Audit, Page
from ..cases.models import Case

PAGE_TITLES_BY_URL = {
    "/": "Home",
    "/accounts/login/": "Sign in",
    "/accounts/password_reset/": "Reset password",
    "/accounts/password_reset/done/": "Password reset done",
    "/audits/[id]/audit-retest-detail/": "View 12-week test",
    "/audits/[id]/detail/": "View test",
    "/audits/[id]/edit-audit-metadata/": "Test metadata",
    "/audits/[id]/edit-audit-report-options/": "Report options",
    "/audits/[id]/edit-audit-report-text/": "Report text",
    "/audits/[id]/edit-audit-retest-metadata/": "12-week test metadata",
    "/audits/[id]/edit-audit-retest-pages/": "12-week pages comparison",
    "/audits/[id]/edit-audit-retest-statement-decision/": "12-week accessibility statement compliance decision",
    "/audits/[id]/edit-audit-statement-1/": "Accessibility statement Pt. 1",
    "/audits/[id]/edit-audit-statement-2/": "Accessibility statement Pt. 2",
    "/audits/[id]/edit-audit-summary/": "Test summary",
    "/audits/[id]/edit-audit-pages/": "Pages",
    "/audits/[id]/edit-retest-website-decision/": "12-week website compliance decision",
    "/audits/[id]/edit-statement-decision/": "Accessibility statement compliance decision",
    "/audits/[id]/edit-website-decision/": "Website compliance decision",
    "/audits/create-for-case/[id]/": "Create test",
    "/audits/pages/[id]/edit-audit-page-checks/": "Testing",
    "/audits/pages/[id]/edit-audit-retest-page-checks/": "Retesting",
    "/audits/wcag-definition-create/": "Create WCAG error",
    "/audits/wcag-definition-list/": "WCAG errors editor",
    "/audits/[id]/edit-wcag-definition/": "WCAG error editor",
    "/cases/": "Search",
    "/cases/[id]/edit-case-close/": "Closing the case",
    "/cases/[id]/edit-case-details/": "Case details",
    "/cases/[id]/edit-contact-details/": "Contact details",
    "/cases/[id]/edit-enforcement-body-correspondence/": "Equality body summary",
    "/cases/[id]/edit-no-psb-response/": "Public sector body is unresponsive",
    "/cases/[id]/edit-post-case/": "Post case summary",
    "/cases/[id]/edit-qa-process/": "QA process",
    "/cases/[id]/edit-report-correspondence/": "Report correspondence",
    "/cases/[id]/edit-report-details/": "Report details",
    "/cases/[id]/edit-report-followup-due-dates/": "Report followup dates",
    "/cases/[id]/edit-review-changes/": "Reviewing changes",
    "/cases/[id]/edit-test-results/": "Testing details",
    "/cases/[id]/edit-twelve-week-correspondence-due-dates/": "12-week correspondence dates",
    "/cases/[id]/edit-twelve-week-correspondence/": "12-week correspondence",
    "/cases/[id]/twelve-week-correspondence-email/": "Email template",
    "/cases/[id]/edit-twelve-week-retest/": "12-week retest",
    "/cases/[id]/view/": "View case",
    "/cases/create/": "Create case",
    "/common/contact/": "Contact admin",
    "/common/edit-active-qa-auditor/": "Active QA auditor",
    "/common/markdown-cheatsheet/": "Markdown cheatsheet",
    "/common/more-information/": "More information about monitoring",
    "/common/metrics-case/": "Case metrics",
    "/common/metrics-policy/": "Policy metrics",
    "/common/metrics-report/": "Report metrics",
    "/common/platform-versions/": "Platform version history",
    "/common/report-issue/": "Report an issue",
    "/notifications/notifications-list/": "Comments",
    "/overdue/overdue-list/": "Overdue",
    "/reminders/cases/[id]/reminder-create/": "Reminder",
    "/reminders/reminder-list/": "Reminders",
    "/reports/edit-report-wrapper/": "Report viewer editor",
    "/reports/[id]/report-publisher/": "Report publisher",
    "/reports/[id]/edit-report/": "Edit report",
    "/reports/[id]/edit-report-metadata/": "Report metadata",
    "/reports/[id]/report-metrics-view/": "Report visit logs",
    "/reports/sections/[id]/edit-section/": "Report section update",
    "/user/[id]/edit-user/": "Account details",
    "/user/register/": "Register",
}


def get_page_title(path: str) -> str:  # noqa: C901
    """Derive page title from path"""
    path_without_id = re.sub(r"/\d+/", "/[id]/", path)
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
    elif path_without_id.startswith("/audits/[id]/"):
        try:
            audit: Audit = Audit.objects.get(id=path.split("/")[2])
            page_title: str = f"{audit.case.organisation_name} | {page_heading}"
        except Audit.DoesNotExist:
            pass
    elif path_without_id.startswith("/audits/pages/[id]/"):
        try:
            page: Page = Page.objects.get(id=path.split("/")[3])
            page_title: str = (
                f"{page.audit.case.organisation_name} | {page_heading} {page}"
            )
        except Page.DoesNotExist:
            pass
    elif path_without_id == "/reminders/cases/[id]/reminder-create/":
        try:
            case: Case = Case.objects.get(id=path.split("/")[3])
            page_title: str = f"{case.organisation_name} | {page_heading}"
        except Case.DoesNotExist:
            pass
    elif path_without_id == "/audits/create-for-case/[id]/":
        try:
            case: Case = Case.objects.get(id=path.split("/")[3])
            page_title: str = f"{case.organisation_name} | {page_heading}"
        except Case.DoesNotExist:
            pass
    return page_title
