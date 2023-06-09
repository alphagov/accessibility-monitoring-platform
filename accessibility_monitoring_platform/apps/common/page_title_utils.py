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
    "/audits/[id]/edit-audit-retest-statement-1/": "12-week accessibility statement Pt. 1",
    "/audits/[id]/edit-audit-12-week-statement/": "Append accessibility statement",
    "/audits/[id]/edit-audit-retest-statement-2/": "12-week accessibility statement Pt. 2",
    "/audits/[id]/edit-statement-decision/": "Accessibility statement compliance decision",
    "/audits/[id]/edit-website-decision/": "Website compliance decision",
    "/audits/[id]/edit-statement-overview/": "Statement overview",
    "/audits/[id]/edit-statement-website/": "Accessibility statement information",
    "/audits/[id]/edit-statement-compliance/": "Compliance status",
    "/audits/[id]/edit-statement-non-accessible/": "Non accessible content",
    "/audits/[id]/edit-statement-preparation/": "Statement preparation",
    "/audits/[id]/edit-statement-feedback/": "Feedback and contact information",
    "/audits/[id]/edit-statement-enforcement/": "Enforcement procedure",
    "/audits/[id]/edit-statement-other/": "Other",
    "/audits/[id]/edit-retest-statement-overview/": "12-week accessibility statement overview",
    "/audits/[id]/edit-retest-statement-website/": "12-week accessibility statement website",
    "/audits/[id]/edit-retest-statement-compliance/": "12-week accessibility statement compliance",
    "/audits/[id]/edit-retest-statement-non-accessible/": "12-week accessibility statement non-accessible",
    "/audits/[id]/edit-retest-statement-preparation/": "12-week accessibility statement preparation",
    "/audits/[id]/edit-retest-statement-feedback/": "12-week accessibility statement feedback",
    "/audits/[id]/edit-retest-statement-enforcement/": "12-week accessibility statement enforcement",
    "/audits/[id]/edit-retest-statement-other/": "12-week accessibility statement other",
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
    "/common/edit-frequently-used-links/": "Edit frequently used links",
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
    "/reports/[id]/edit-report-notes/": "Report notes",
    "/reports/[id]/report-metrics-view/": "Report visit logs",
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
            page_title: str = f"Case does not exist: {path}"
    elif path_without_id.startswith("/audits/[id]/"):
        try:
            audit: Audit = Audit.objects.get(id=path.split("/")[2])
            page_title: str = f"{audit.case.organisation_name} | {page_heading}"
        except Audit.DoesNotExist:
            page_title: str = f"Audit does not exist: {path}"
    elif path_without_id.startswith("/audits/pages/[id]/"):
        try:
            page: Page = Page.objects.get(id=path.split("/")[3])
            page_title: str = (
                f"{page.audit.case.organisation_name} | {page_heading} {page}"
            )
        except Page.DoesNotExist:
            page_title: str = f"Page does not exist: {path}"
    elif path_without_id == "/reminders/cases/[id]/reminder-create/":
        try:
            case: Case = Case.objects.get(id=path.split("/")[3])
            page_title: str = f"{case.organisation_name} | {page_heading}"
        except Case.DoesNotExist:
            page_title: str = f"Case does not exist: {path}"
    elif path_without_id == "/audits/create-for-case/[id]/":
        try:
            case: Case = Case.objects.get(id=path.split("/")[3])
            page_title: str = f"{case.organisation_name} | {page_heading}"
        except Case.DoesNotExist:
            page_title: str = f"Case does not exist: {path}"
    return page_title
