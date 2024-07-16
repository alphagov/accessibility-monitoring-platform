from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import resolve, reverse

from ..audits.models import Page, RetestPage
from ..cases.models import Case


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
}


def get_amp_page_name(request: HttpRequest) -> str:
    """Lookup and return the name of the requested page"""
    url_name: str = resolve(request.path_info).view_name
    if url_name in ALL_PAGE_NAMES:
        page_name: PageName = ALL_PAGE_NAMES.get(url_name)
    else:
        return f"Page name not found for {url_name}"

    if url_name == "audits:edit-audit-page-checks":
        page_id: int = int(request.path.split("/")[3])
        page: Page = Page.objects.get(id=page_id)
        return page_name.get_name(page=page)
    if url_name == "audits:edit-retest-page-checks":
        retest_page_id: int = int(request.path.split("/")[3])
        retest_page: RetestPage = RetestPage.objects.get(id=retest_page_id)
        return page_name.get_name(retest_page=retest_page)

    return page_name.get_name()


class CaseNavContextMixin:
    """Mixin to populate context for case navigation"""

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add case navigation values into context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        if "case" in context:
            case: Case = context["case"]
        else:
            case: Optional[Case] = None
            if hasattr(self, "object") and self.object is not None:
                if isinstance(self.object, Case):
                    case: Case = self.object
                elif hasattr(self.object, "case"):
                    case: Case = self.object.case
                elif hasattr(self.object, "audit"):
                    case: Case = self.object.audit.case
            elif hasattr(self, "page"):
                case: Case = self.page.audit.case
            elif "case_id" in self.kwargs:
                case: Case = get_object_or_404(Case, id=self.kwargs.get("case_id"))
            if case is not None:
                context["case"] = case

        if case is not None:
            context["case_nav_sections"] = build_case_nav_sections(case=case)

        return context


@dataclass
class NavSubPage:
    url_name: str
    url_kwargs: Optional[Dict[str, Any]] = None
    name_kwargs: Optional[Dict[str, Any]] = None
    complete: bool = False

    def url(self):
        if self.url_kwargs is None:
            return reverse(self.url_name)
        return reverse(self.url_name, kwargs=self.url_kwargs)

    def name(self):
        if self.url_name in ALL_PAGE_NAMES:
            if self.name_kwargs is None:
                return ALL_PAGE_NAMES.get(self.url_name).get_name()
            return ALL_PAGE_NAMES.get(self.url_name).get_name(**self.name_kwargs)
        return f"No page name found for {self.url_name}"


@dataclass
class NavPage:
    url_name: str
    url_kwargs: Optional[Dict[str, Any]] = None
    complete: bool = False
    subpages: Optional[List[NavSubPage]] = None

    def url(self):
        if self.url_kwargs is None:
            return reverse(self.url_name)
        return reverse(self.url_name, kwargs=self.url_kwargs)

    def name(self):
        if self.url_name in ALL_PAGE_NAMES:
            return ALL_PAGE_NAMES.get(self.url_name).get_name()
        return f"No page name found for {self.url_name}"


@dataclass
class NavSection:
    name: str
    disabled: bool = False
    pages: Optional[List[NavPage]] = None

    def number_pages_and_subpages(self) -> int:
        if self.pages is not None:
            counter: int = len(self.pages)
            for page in self.pages:
                if page.subpages is not None:
                    counter += len(page.subpages)
            return counter
        return 0

    def number_complete(self) -> int:
        if self.pages is not None:
            counter: int = 0
            for page in self.pages:
                if page.complete:
                    counter += 1
                if page.subpages is not None:
                    counter += len(
                        [subpage for subpage in page.subpages if subpage.complete]
                    )
            return counter
        return 0


def build_case_nav_sections(case: Case) -> List[NavSection]:
    """Return list of case sections for navigation details elements"""
    kwargs_case_pk: Dict[str, int] = {"pk": case.id}
    if case.audit is not None:
        kwargs_audit_pk: Dict[str, int] = {"pk": case.audit.id}
        audit_nav_sections: List[NavSection] = [
            NavSection(
                name="Initial WCAG test",
                pages=[
                    NavPage(
                        url_name="audits:edit-audit-metadata",
                        url_kwargs=kwargs_audit_pk,
                        complete=case.audit.audit_metadata_complete_date,
                    ),
                    NavPage(
                        url_name="audits:edit-audit-pages",
                        url_kwargs=kwargs_audit_pk,
                        complete=case.audit.audit_pages_complete_date,
                        subpages=[
                            NavSubPage(
                                url_name="audits:edit-audit-page-checks",
                                url_kwargs={"pk": page.id},
                                name_kwargs={"page": page},
                                complete=page.complete_date,
                            )
                            for page in case.audit.testable_pages
                        ],
                    ),
                    NavPage(
                        url_name="audits:edit-website-decision",
                        url_kwargs=kwargs_audit_pk,
                        complete=case.audit.audit_website_decision_complete_date,
                    ),
                    NavPage(
                        url_name="audits:edit-audit-wcag-summary",
                        url_kwargs=kwargs_audit_pk,
                        complete=case.audit.audit_summary_complete_date,
                    ),
                ],
            ),
            NavSection(
                name="Initial statement",
                pages=[
                    NavPage(
                        url_name="audits:edit-statement-pages",
                        url_kwargs=kwargs_audit_pk,
                        complete=case.audit.audit_statement_pages_complete_date,
                    ),
                    NavPage(
                        url_name="audits:edit-statement-overview",
                        url_kwargs=kwargs_audit_pk,
                        complete=case.audit.audit_statement_overview_complete_date,
                        subpages=[
                            NavSubPage(
                                url_name="audits:edit-statement-website",
                                url_kwargs=kwargs_audit_pk,
                                complete=case.audit.audit_statement_website_complete_date,
                            ),
                            NavSubPage(
                                url_name="audits:edit-statement-compliance",
                                url_kwargs=kwargs_audit_pk,
                                complete=case.audit.audit_statement_compliance_complete_date,
                            ),
                            NavSubPage(
                                url_name="audits:edit-statement-non-accessible",
                                url_kwargs=kwargs_audit_pk,
                                complete=case.audit.audit_statement_non_accessible_complete_date,
                            ),
                            NavSubPage(
                                url_name="audits:edit-statement-preparation",
                                url_kwargs=kwargs_audit_pk,
                                complete=case.audit.audit_statement_preparation_complete_date,
                            ),
                            NavSubPage(
                                url_name="audits:edit-statement-feedback",
                                url_kwargs=kwargs_audit_pk,
                                complete=case.audit.audit_statement_feedback_complete_date,
                            ),
                            NavSubPage(
                                url_name="audits:edit-statement-custom",
                                url_kwargs=kwargs_audit_pk,
                                complete=case.audit.audit_statement_custom_complete_date,
                            ),
                        ],
                    ),
                    NavPage(
                        url_name="audits:edit-initial-disproportionate-burden",
                        url_kwargs=kwargs_audit_pk,
                        complete=case.audit.initial_disproportionate_burden_complete_date,
                    ),
                    NavPage(
                        url_name="audits:edit-statement-decision",
                        url_kwargs=kwargs_audit_pk,
                        complete=case.audit.audit_statement_decision_complete_date,
                    ),
                    NavPage(
                        url_name="audits:edit-audit-statement-summary",
                        url_kwargs=kwargs_audit_pk,
                        complete=case.audit.audit_summary_complete_date,
                    ),
                ],
            ),
        ]
    else:
        audit_nav_sections: List[NavSection] = []
    return [
        NavSection(
            name="Case details",
            pages=[
                NavPage(
                    url_name="cases:edit-case-metadata",
                    url_kwargs=kwargs_case_pk,
                    complete=case.case_details_complete_date,
                )
            ],
        ),
    ] + audit_nav_sections
