from dataclasses import dataclass
from typing import Dict

from django.http import HttpRequest
from django.urls import URLResolver, resolve

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
    "audits:edit-audit-metadata": PageName("Test metadata"),
    "audits:edit-audit-page-checks": PageName(
        "{page.page_title} test", format_string=True
    ),
    "audits:edit-audit-pages": PageName("Pages"),
    "audits:edit-audit-report-options": PageName("Report options"),
    "audits:edit-audit-retest-metadata": PageName("12-week test metadata"),
    "audits:edit-audit-retest-page-checks": PageName(
        "Retesting {page}", format_string=True
    ),
    "audits:edit-audit-retest-pages-comparison": PageName("12-week pages comparison"),
    "audits:edit-audit-retest-statement-1": PageName(
        "12-week accessibility statement Pt. 1"
    ),
    "audits:edit-audit-retest-statement-2": PageName(
        "12-week accessibility statement Pt. 2"
    ),
    "audits:edit-audit-retest-statement-comparison": PageName(
        "12-week accessibility statement comparison"
    ),
    "audits:edit-audit-retest-statement-decision": PageName(
        "12-week statement compliance decision"
    ),
    "audits:edit-audit-retest-statement-pages": PageName("12-week statement links"),
    "audits:edit-audit-retest-website-decision": PageName(
        "12-week website compliance decision"
    ),
    "audits:edit-audit-statement-1": PageName("Accessibility statement Pt. 1"),
    "audits:edit-audit-statement-2": PageName("Accessibility statement Pt. 2"),
    "audits:edit-audit-statement-summary": PageName("Test summary"),
    "audits:edit-audit-wcag-summary": PageName("Test summary"),
    "audits:edit-equality-body-disproportionate-burden": PageName(
        "Disproportionate burden"
    ),
    "audits:edit-equality-body-statement-compliance": PageName("Compliance status"),
    "audits:edit-equality-body-statement-custom": PageName("Custom statement issues"),
    "audits:edit-equality-body-statement-decision": PageName("Statement decision"),
    "audits:edit-equality-body-statement-feedback": PageName(
        "Feedback and enforcement procedure"
    ),
    "audits:edit-equality-body-statement-non-accessible": PageName(
        "Non-accessible content"
    ),
    "audits:edit-equality-body-statement-overview": PageName("Statement overview"),
    "audits:edit-equality-body-statement-pages": PageName("Statement links"),
    "audits:edit-equality-body-statement-preparation": PageName(
        "Statement preparation"
    ),
    "audits:edit-equality-body-statement-results": PageName("Statement results"),
    "audits:edit-equality-body-statement-website": PageName("Statement information"),
    "audits:edit-initial-disproportionate-burden": PageName(
        "Initial disproportionate burden claim"
    ),
    "audits:edit-retest-page-checks": PageName(
        "Retest #{retest_page.retest.id_within_case} | {retest_page}",
        format_string=True,
    ),
    "audits:edit-retest-statement-compliance": PageName("12-week compliance status"),
    "audits:edit-retest-statement-custom": PageName("12-week custom statement issues"),
    "audits:edit-retest-statement-feedback": PageName(
        "12-week feedback and enforcement procedure"
    ),
    "audits:edit-retest-statement-non-accessible": PageName(
        "12-week non-accessible content"
    ),
    "audits:edit-retest-statement-overview": PageName("12-week statement overview"),
    "audits:edit-retest-statement-preparation": PageName(
        "12-week statement preparation"
    ),
    "audits:edit-retest-statement-website": PageName("12-week statement information"),
    "audits:edit-statement-compliance": PageName("Compliance status"),
    "audits:edit-statement-custom": PageName("Custom statement issues"),
    "audits:edit-statement-decision": PageName("Initial statement compliance decision"),
    "audits:edit-statement-feedback": PageName("Feedback and enforcement procedure"),
    "audits:edit-statement-non-accessible": PageName("Non-accessible content"),
    "audits:edit-statement-overview": PageName("Statement overview"),
    "audits:edit-statement-pages": PageName("Statement links"),
    "audits:edit-statement-preparation": PageName("Statement preparation"),
    "audits:edit-statement-website": PageName("Statement information"),
    "audits:edit-twelve-week-disproportionate-burden": PageName(
        "12-week disproportionate burden claim"
    ),
    "audits:edit-website-decision": PageName("Website compliance decision"),
    "audits:retest-comparison-update": PageName("Comparison"),
    "audits:retest-compliance-update": PageName("Compliance decision"),
    "audits:retest-metadata-update": PageName("Retest metadata"),
    "audits:statement-check-list": PageName("Statement issues editor"),
    "audits:wcag-definition-list": PageName("WCAG errors editor"),
    "cases:create-equality-body-correspondence": PageName("Add Zendesk ticket"),
    "cases:create-zendesk-ticket": PageName("Add PSB Zendesk ticket"),
    "cases:deactivate-case": PageName("Deactivate case"),
    "cases:edit-12-week-update-request-ack": PageName(
        "12-week update request acknowledged"
    ),
    "cases:edit-12-week-update-requested": PageName("12-week update requested"),
    "cases:edit-case-close": PageName("Closing the case"),
    "cases:edit-case-metadata": PageName("Case metadata"),
    "cases:edit-contact-details": PageName("Contact details"),
    "cases:edit-cores-overview": PageName("Correspondence overview"),
    "cases:edit-enforcement-recommendation": PageName("Enforcement recommendation"),
    "cases:edit-equality-body-correspondence": PageName("Edit Zendesk ticket"),
    "cases:edit-equality-body-metadata": PageName("Equality body metadata"),
    "cases:edit-find-contact-details": PageName("Find contact details"),
    "cases:edit-four-week-followup": PageName("Four week follow-up"),
    "cases:edit-no-psb-response": PageName("Public sector body is unresponsive"),
    "cases:edit-one-week-followup": PageName("One week follow-up"),
    "cases:edit-one-week-followup-final": PageName(
        "One week follow-up for final update"
    ),
    "cases:edit-post-case": PageName("Post case summary"),
    "cases:edit-publish-report": PageName("Publish report"),
    "cases:edit-qa-comments": PageName("QA comments"),
    "cases:edit-report-acknowledged": PageName("Report acknowledged"),
    "cases:edit-report-approved": PageName("Report approved"),
    "cases:edit-report-details": PageName("Report details"),
    "cases:edit-report-sent-on": PageName("Report sent on"),
    "cases:edit-retest-overview": PageName("Retest overview"),
    "cases:edit-review-changes": PageName("Reviewing changes"),
    "cases:edit-statement-enforcement": PageName("Statement enforcement"),
    "cases:edit-test-results": PageName("Testing details"),
    "cases:edit-twelve-week-retest": PageName("12-week retest"),
    "cases:email-template-list": PageName("Email templates"),
    "cases:email-template-preview": PageName(
        "{email_template.name}", format_string=True
    ),
    "cases:legacy-end-of-case": PageName("Legacy end of case data"),
    "cases:list-equality-body-correspondence": PageName(
        "All equality body correspondence"
    ),
    "cases:outstanding-issues": PageName("Outstanding issues"),
    "cases:reactivate-case": PageName("Reactivate case"),
    "cases:retest-create-error": PageName("Cannot start new retest"),
    "cases:status-workflow": PageName("Status workflow"),
    "cases:update-zendesk-ticket": PageName("Edit PSB Zendesk ticket"),
    "cases:zendesk-tickets": PageName("PSB Zendesk tickets"),
    "comments:edit-qa-comment": PageName("Edit or delete comment"),
    "common:bulk-url-search": PageName("Bulk URL search"),
    "common:edit-active-qa-auditor": PageName("Active QA auditor"),
    "common:edit-footer-links": PageName("Edit footer links"),
    "common:edit-frequently-used-links": PageName("Edit frequently used links"),
    "common:email-template-list": PageName("Email template manager"),
    "common:email-template-preview": PageName(
        "{email_template.name} preview", format_string=True
    ),
    "common:markdown-cheatsheet": PageName("Markdown cheatsheet"),
    "common:metrics-case": PageName("Case metrics"),
    "common:metrics-policy": PageName("Policy metrics"),
    "common:metrics-report": PageName("Report metrics"),
    "common:more-information": PageName("More information about monitoring"),
    "common:platform-history": PageName("Platform version history"),
    "notifications:edit-reminder-task": PageName("Reminder"),
    "notifications:reminder-create": PageName("Reminder"),
    "reports:edit-report-notes": PageName("Report notes"),
    "reports:edit-report-wrapper": PageName("Report viewer editor"),
    "reports:report-confirm-publish": PageName("Publish report"),
    "reports:report-metrics-view": PageName("Report visit logs"),
    "reports:report-publisher": PageName("Report publisher"),
    "users:edit-user": PageName("Account details"),
}


def get_amp_page_name(request: HttpRequest) -> str:
    """Lookup and return the name of the requested page"""
    url_resolver: URLResolver = resolve(request.path_info)
    url_name: str = url_resolver.view_name
    if url_name in ALL_PAGE_NAMES:
        page_name: PageName = ALL_PAGE_NAMES.get(url_name)
    else:
        return f"Page name not found for {url_name}"

    if url_name in [
        "audits:edit-audit-page-checks",
        "audits:edit-audit-retest-page-checks",
    ]:
        page_id: int = url_resolver.kwargs["pk"]
        page: Page = Page.objects.get(id=page_id)
        return page_name.get_name(page=page)
    if url_name == "audits:edit-retest-page-checks":
        retest_page_id: int = url_resolver.kwargs["pk"]
        retest_page: RetestPage = RetestPage.objects.get(id=retest_page_id)
        return page_name.get_name(retest_page=retest_page)
    if url_name in ["cases:email-template-preview", "common:email-template-preview"]:
        email_template_id: int = url_resolver.kwargs["pk"]
        email_template: EmailTemplate = EmailTemplate.objects.get(id=email_template_id)
        return page_name.get_name(email_template=email_template)

    return page_name.get_name()
