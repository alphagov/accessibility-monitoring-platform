from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import resolve, reverse

from ..audits.models import Page
from ..cases.models import Case

ALL_PAGE_NAMES: Dict[str, str] = {
    "cases:edit-case-metadata": "Case metadata",
    "audits:edit-audit-metadata": "Initial test metadata",
    "audits:edit-audit-pages": "Add or remove pages",
    "audits:edit-audit-page-checks": "test",
    "audits:edit-website-decision": "Website compliance decision",
    "audits:edit-audit-wcag-summary": "Test summary",
    "audits:edit-statement-pages": "Statement links",
    "audits:edit-statement-overview": "Statement overview",
    "audits:edit-statement-website": "Statement information",
    "audits:edit-statement-compliance": "Compliance status",
    "audits:edit-statement-non-accessible": "Non-accessible content",
    "audits:edit-statement-preparation": "Statement preparation",
    "audits:edit-statement-feedback": "Feedback and enforcement procedure",
    "audits:edit-statement-custom": "Custom statement issues",
    "audits:edit-initial-disproportionate-burden": "Initial disproportionate burden claim",
    "audits:edit-statement-decision": "Initial statement compliance decision",
    "audits:edit-audit-statement-summary": "Test summary",
}


def get_amp_page_name(request: HttpRequest) -> str:
    """Lookup and return the name of the requested page"""
    url_name: str = resolve(request.path_info).view_name
    if url_name == "audits:edit-audit-page-checks":
        page_id: int = int(request.path.split("/")[3])
        page: Page = Page.objects.get(id=page_id)
        return f"{page.page_title} {ALL_PAGE_NAMES.get(url_name)}"
    return ALL_PAGE_NAMES.get(url_name, f"Page name not found for {url_name}")


class CaseNavContextMixin:
    """Mixin to populate context for case navigation"""

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add case navigation values into context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        if "case" in context:
            case: Case = context["case"]
        else:
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
            context["case"] = case

        if case is not None:
            context["case_nav_sections"] = build_case_nav_sections(case=case)

        return context


@dataclass
class NavSubPage:
    name: str
    url: str
    complete: bool


@dataclass
class NavPage:
    name: str
    url: str
    complete: bool
    subpages: Optional[List[NavSubPage]] = None


@dataclass
class NavSection:
    name: str
    disabled: bool = False
    pages: Optional[List[NavPage]] = None

    def number_complete(self) -> int:
        if self.pages is not None:
            return len([page for page in self.pages if page.complete])
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
                        name=ALL_PAGE_NAMES.get("audits:edit-audit-metadata"),
                        url=reverse(
                            "audits:edit-audit-metadata", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_metadata_complete_date,
                    ),
                    NavPage(
                        name=ALL_PAGE_NAMES.get("audits:edit-audit-pages"),
                        url=reverse("audits:edit-audit-pages", kwargs=kwargs_audit_pk),
                        complete=case.audit.audit_pages_complete_date,
                        subpages=[
                            NavSubPage(
                                name=f"{page.page_title} {ALL_PAGE_NAMES.get('audits:edit-audit-page-checks')}",
                                url=reverse(
                                    "audits:edit-audit-page-checks",
                                    kwargs={"pk": page.id},
                                ),
                                complete=page.complete_date,
                            )
                            for page in case.audit.testable_pages
                        ],
                    ),
                    NavPage(
                        name=ALL_PAGE_NAMES.get("audits:edit-website-decision"),
                        url=reverse(
                            "audits:edit-website-decision", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_website_decision_complete_date,
                    ),
                    NavPage(
                        name=ALL_PAGE_NAMES.get("audits:edit-audit-wcag-summary"),
                        url=reverse(
                            "audits:edit-audit-wcag-summary", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_summary_complete_date,
                    ),
                ],
            ),
            NavSection(
                name="Initial statement",
                pages=[
                    NavPage(
                        name=ALL_PAGE_NAMES.get("audits:edit-statement-pages"),
                        url=reverse(
                            "audits:edit-statement-pages", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_statement_pages_complete_date,
                    ),
                    NavPage(
                        name=ALL_PAGE_NAMES.get("audits:edit-statement-overview"),
                        url=reverse(
                            "audits:edit-statement-overview", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_statement_overview_complete_date,
                        subpages=[
                            NavSubPage(
                                name=ALL_PAGE_NAMES.get(
                                    "audits:edit-statement-website"
                                ),
                                url=reverse(
                                    "audits:edit-statement-website",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_website_complete_date,
                            ),
                            NavSubPage(
                                name=ALL_PAGE_NAMES.get(
                                    "audits:edit-statement-compliance"
                                ),
                                url=reverse(
                                    "audits:edit-statement-compliance",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_compliance_complete_date,
                            ),
                            NavSubPage(
                                name=ALL_PAGE_NAMES.get(
                                    "audits:edit-statement-non-accessible"
                                ),
                                url=reverse(
                                    "audits:edit-statement-non-accessible",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_non_accessible_complete_date,
                            ),
                            NavSubPage(
                                name=ALL_PAGE_NAMES.get(
                                    "audits:edit-statement-preparation"
                                ),
                                url=reverse(
                                    "audits:edit-statement-preparation",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_preparation_complete_date,
                            ),
                            NavSubPage(
                                name=ALL_PAGE_NAMES.get(
                                    "audits:edit-statement-feedback"
                                ),
                                url=reverse(
                                    "audits:edit-statement-feedback",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_feedback_complete_date,
                            ),
                            NavSubPage(
                                name=ALL_PAGE_NAMES.get("audits:edit-statement-custom"),
                                url=reverse(
                                    "audits:edit-statement-custom",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_custom_complete_date,
                            ),
                        ],
                    ),
                    NavPage(
                        name=ALL_PAGE_NAMES.get(
                            "audits:edit-initial-disproportionate-burden"
                        ),
                        url=reverse(
                            "audits:edit-initial-disproportionate-burden",
                            kwargs=kwargs_audit_pk,
                        ),
                        complete=case.audit.initial_disproportionate_burden_complete_date,
                    ),
                    NavPage(
                        name=ALL_PAGE_NAMES.get("audits:edit-statement-decision"),
                        url=reverse(
                            "audits:edit-statement-decision", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_statement_decision_complete_date,
                    ),
                    NavPage(
                        name=ALL_PAGE_NAMES.get("audits:edit-audit-statement-summary"),
                        url=reverse(
                            "audits:edit-audit-statement-summary",
                            kwargs=kwargs_audit_pk,
                        ),
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
                    name=ALL_PAGE_NAMES.get("cases:edit-case-metadata"),
                    url=reverse("cases:edit-case-metadata", kwargs=kwargs_case_pk),
                    complete=case.case_details_complete_date,
                )
            ],
        ),
    ] + audit_nav_sections
