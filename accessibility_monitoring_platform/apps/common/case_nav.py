from dataclasses import dataclass
from typing import Dict

from django.http import HttpRequest
from django.urls import resolve

from ..audits.models import Page, RetestPage
from ..common.models import EmailTemplate


@dataclass
class PageName:
    name: str
    format_string: bool = False

    def get_name(self, **kwargs):
        if self.format_string is True:
            return self.name.format(**kwargs)
        return self.name


ALL_PAGE_NAMES: Dict[str, PageName] = {
    "cases:edit-case-metadata": PageName("Case metadata"),
    "audits:edit-audit-metadata": PageName("Initial test metadata"),
    "audits:edit-audit-pages": PageName("Add or remove pages"),
    "audits:edit-audit-page-checks": PageName(
        "{page.page_title} test", format_string=True
    ),
    "audits:edit-website-decision": PageName("Website compliance decision"),
    "audits:edit-audit-wcag-summary": PageName("Test summary"),
    "audits:edit-statement-pages": PageName("Statement links"),
    "audits:edit-statement-overview": PageName("Statement overview"),
    "audits:edit-statement-website": PageName("Statement information"),
    "audits:edit-statement-compliance": PageName("Compliance status"),
    "audits:edit-statement-non-accessible": PageName("Non-accessible content"),
    "audits:edit-statement-preparation": PageName("Statement preparation"),
    "audits:edit-statement-feedback": PageName("Feedback and enforcement procedure"),
    "audits:edit-statement-custom": PageName("Custom statement issues"),
    "audits:edit-initial-disproportionate-burden": PageName(
        "Initial disproportionate burden claim"
    ),
    "audits:edit-statement-decision": PageName("Initial statement compliance decision"),
    "audits:edit-audit-statement-summary": PageName("Test summary"),
    "cases:zendesk-tickets": PageName("PSB Zendesk tickets"),
    "cases:create-zendesk-ticket": PageName("Add PSB Zendesk ticket"),
    "cases:update-zendesk-ticket": PageName("Edit PSB Zendesk ticket"),
    "notifications:reminder-create": PageName("Reminder"),
    "notifications:edit-reminder-task": PageName("Reminder"),
    "cases:edit-12-week-update-request-ack": PageName(
        "12-week update request acknowledged"
    ),
    "cases:edit-12-week-update-requested": PageName("12-week update requested"),
    "cases:edit-case-close": PageName("Closing the case"),
    "cases:edit-contact-details": PageName("Contact details"),
    "comments:edit-qa-comment": PageName("Edit or delete comment"),
    "audits:edit-audit-retest-statement-2": PageName(
        "12-week accessibility statement Pt. 2"
    ),
    "audits:edit-audit-retest-statement-comparison": PageName(
        "12-week accessibility statement comparison"
    ),
    "audits:edit-retest-page-checks": PageName(
        "Retest #{retest_page.retest.id_within_case} | {retest_page}",
        format_string=True,
    ),
    "audits:edit-equality-body-statement-pages": PageName("Statement links"),
    "audits:retest-comparison-update": PageName("Comparison"),
    "audits:retest-compliance-update": PageName("Compliance decision"),
    "audits:edit-equality-body-disproportionate-burden": PageName(
        "Disproportionate burden"
    ),
    "audits:retest-metadata-update": PageName("Retest metadata"),
    "audits:edit-equality-body-statement-decision": PageName("Statement decision"),
    "audits:edit-equality-body-statement-results": PageName("Statement results"),
    "audits:edit-audit-report-options": PageName("Report options"),
    "audits:edit-audit-retest-statement-1": PageName(
        "12-week accessibility statement Pt. 1"
    ),
    "audits:edit-audit-retest-statement-decision": PageName(
        "12-week statement compliance decision"
    ),
    "audits:edit-audit-retest-website-decision": PageName(
        "12-week website compliance decision"
    ),
    "audits:edit-audit-statement-1": PageName("Accessibility statement Pt. 1"),
    "audits:edit-audit-statement-2": PageName("Accessibility statement Pt. 2"),
    "audits:edit-twelve-week-disproportionate-burden": PageName(
        "12-week disproportionate burden claim"
    ),
    "audits:edit-audit-retest-pages-comparison": PageName("12-week pages comparison"),
    "audits:edit-audit-retest-metadata": PageName("12-week test metadata"),
    "audits:edit-audit-retest-page-checks": PageName(
        "Retesting {page}", format_string=True
    ),
    "audits:edit-audit-retest-statement-pages": PageName("12-week statement links"),
    "audits:statement-check-list": PageName("Statement issues editor"),
    "audits:edit-equality-body-statement-compliance": PageName("Compliance status"),
    "audits:edit-equality-body-statement-custom": PageName("Custom statement issues"),
    "audits:edit-equality-body-statement-feedback": PageName(
        "Feedback and enforcement procedure"
    ),
    "audits:edit-equality-body-statement-non-accessible": PageName(
        "Non-accessible content"
    ),
    "audits:edit-equality-body-statement-overview": PageName("Statement overview"),
    "audits:edit-equality-body-statement-preparation": PageName(
        "Statement preparation"
    ),
    "audits:edit-equality-body-statement-website": PageName("Statement information"),
    "audits:edit-retest-statement-compliance": PageName("12-week compliance status"),
    "audits:edit-retest-statement-feedback": PageName(
        "12-week feedback and enforcement procedure"
    ),
    "audits:edit-retest-statement-non-accessible": PageName(
        "12-week non-accessible content"
    ),
    "audits:edit-retest-statement-custom": PageName("12-week custom statement issues"),
    "audits:edit-retest-statement-overview": PageName("12-week statement overview"),
    "audits:edit-retest-statement-preparation": PageName(
        "12-week statement preparation"
    ),
    "audits:edit-retest-statement-website": PageName("12-week statement information"),
    "audits:wcag-definition-list": PageName("WCAG errors editor"),
    "cases:email-template-list": PageName("Email templates"),
    "cases:email-template-preview": PageName(
        "{email_template.name}", format_string=True
    ),
    "cases:edit-cores-overview": PageName("Correspondence overview"),
    "cases:deactivate-case": PageName("Deactivate case"),
    "cases:edit-enforcement-recommendation": PageName("Enforcement recommendation"),
    "cases:create-equality-body-correspondence": PageName("Add Zendesk ticket"),
    "cases:list-equality-body-correspondence": PageName(
        "All equality body correspondence"
    ),
    "cases:edit-equality-body-correspondence": PageName("Edit Zendesk ticket"),
    "cases:edit-equality-body-metadata": PageName("Equality body metadata"),
}


def get_amp_page_name(request: HttpRequest) -> str:
    """Lookup and return the name of the requested page"""
    url_name: str = resolve(request.path_info).view_name
    if url_name in ALL_PAGE_NAMES:
        page_name: PageName = ALL_PAGE_NAMES.get(url_name)
    else:
        return f"Page name not found for {url_name}"

    if url_name in [
        "audits:edit-audit-page-checks",
        "audits:edit-audit-retest-page-checks",
    ]:
        page_id: int = int(request.path.split("/")[3])
        page: Page = Page.objects.get(id=page_id)
        return page_name.get_name(page=page)
    if url_name == "audits:edit-retest-page-checks":
        retest_page_id: int = int(request.path.split("/")[3])
        retest_page: RetestPage = RetestPage.objects.get(id=retest_page_id)
        return page_name.get_name(retest_page=retest_page)
    if url_name == "cases:email-template-preview":
        email_template_id: int = int(request.path.split("/")[3])
        email_template: EmailTemplate = EmailTemplate.objects.get(id=email_template_id)
        return page_name.get_name(email_template=email_template)

    return page_name.get_name()
