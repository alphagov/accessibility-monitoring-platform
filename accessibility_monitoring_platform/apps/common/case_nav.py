from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.shortcuts import get_object_or_404
from django.urls import reverse

from ..cases.models import Case


class CaseNavContextMixin:
    """Mixin to populate context for case navigation"""

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add case navigation values into context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        case: Optional[Case] = None
        if "case" in context:
            case: Case = context["case"]
        elif hasattr(self, "object") and self.object is not None:
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
            context["case_nav_sections"] = build_case_nav_sections(case=case)

        if hasattr(self, "amp_page_name"):
            context["amp_page_name"] = self.amp_page_name

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
                        name="Initial test metadata",
                        url=reverse(
                            "audits:edit-audit-metadata", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_metadata_complete_date,
                    ),
                    NavPage(
                        name="Add or remove pages",
                        url=reverse("audits:edit-audit-pages", kwargs=kwargs_audit_pk),
                        complete=case.audit.audit_pages_complete_date,
                        subpages=[
                            NavSubPage(
                                name=page.test_page_title,
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
                        name="Website compliance decision",
                        url=reverse(
                            "audits:edit-website-decision", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_website_decision_complete_date,
                    ),
                    NavPage(
                        name="Test summary",
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
                        name="Statement links",
                        url=reverse(
                            "audits:edit-statement-pages", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_statement_pages_complete_date,
                    ),
                    NavPage(
                        name="Statement overview",
                        url=reverse(
                            "audits:edit-statement-overview", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_statement_overview_complete_date,
                        subpages=[
                            NavSubPage(
                                name="Statement information",
                                url=reverse(
                                    "audits:edit-statement-website",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_website_complete_date,
                            ),
                            NavSubPage(
                                name="Compliance status",
                                url=reverse(
                                    "audits:edit-statement-compliance",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_compliance_complete_date,
                            ),
                            NavSubPage(
                                name="Non-accessible content",
                                url=reverse(
                                    "audits:edit-statement-non-accessible",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_non_accessible_complete_date,
                            ),
                            NavSubPage(
                                name="Statement preparation",
                                url=reverse(
                                    "audits:edit-statement-preparation",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_preparation_complete_date,
                            ),
                            NavSubPage(
                                name="Feedback and enforcement procedure",
                                url=reverse(
                                    "audits:edit-statement-feedback",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_feedback_complete_date,
                            ),
                            NavSubPage(
                                name="Custom statement issues",
                                url=reverse(
                                    "audits:edit-statement-custom",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_custom_complete_date,
                            ),
                        ],
                    ),
                    NavPage(
                        name="Initial disproportionate burden claim",
                        url=reverse(
                            "audits:edit-initial-disproportionate-burden",
                            kwargs=kwargs_audit_pk,
                        ),
                        complete=case.audit.initial_disproportionate_burden_complete_date,
                    ),
                    NavPage(
                        name="Initial statement compliance decision",
                        url=reverse(
                            "audits:edit-statement-decision", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_statement_decision_complete_date,
                    ),
                    NavPage(
                        name="Test summary",
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
                    name="Case metadata",
                    url=reverse("cases:edit-case-metadata", kwargs=kwargs_case_pk),
                    complete=case.case_details_complete_date,
                )
            ],
        ),
    ] + audit_nav_sections
