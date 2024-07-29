from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

from django.shortcuts import get_object_or_404
from django.urls import reverse

from ..cases.models import Case
from ..common.page_name_utils import get_amp_page_name_by_url


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
            context["closing_the_case_nav_sections"] = (
                build_closing_the_case_nav_sections(case=case)
            )

        return context


class NavPage:
    url: str
    complete: bool = False
    subpages: Optional[List["NavPage"]] = None

    def __init__(
        self,
        url: str,
        complete: Optional[date] = None,
        subpages: Optional[List["NavPage"]] = None,
    ):
        self.url = url
        self.complete = complete is not None
        self.subpages = subpages
        self.name = get_amp_page_name_by_url(url=url)


@dataclass
class NavSection:
    name: str
    disabled: bool = False
    pages: Optional[List[NavPage]] = None

    def number_pages_and_subpages(self) -> int:
        if self.pages is not None:
            count: int = len(self.pages)
            for page in self.pages:
                if page.subpages is not None:
                    count += len(page.subpages)
            return count
        return 0

    def number_complete(self) -> int:
        if self.pages is not None:
            count: int = 0
            for page in self.pages:
                if page.complete:
                    count += 1
                if page.subpages is not None:
                    count += len(
                        [subpage for subpage in page.subpages if subpage.complete]
                    )
            return count
        return 0


def build_case_nav_sections(case: Case) -> List[NavSection]:
    """Return list of case sections for navigation details elements"""
    kwargs_case_pk: Dict[str, int] = {"pk": case.id}
    if case.audit is None:
        audit_nav_sections: List[NavSection] = [
            NavSection(
                name="Initial WCAG test",
                disabled=True,
            ),
            NavSection(
                name="Initial statement",
                disabled=True,
            ),
        ]
    else:
        kwargs_audit_pk: Dict[str, int] = {"pk": case.audit.id}
        audit_nav_sections: List[NavSection] = [
            NavSection(
                name="Initial WCAG test",
                pages=[
                    NavPage(
                        url=reverse(
                            "audits:edit-audit-metadata", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_metadata_complete_date,
                    ),
                    NavPage(
                        url=reverse("audits:edit-audit-pages", kwargs=kwargs_audit_pk),
                        complete=case.audit.audit_pages_complete_date,
                        subpages=[
                            NavPage(
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
                        url=reverse(
                            "audits:edit-website-decision", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_website_decision_complete_date,
                    ),
                    NavPage(
                        url=reverse(
                            "audits:edit-audit-wcag-summary", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_wcag_summary_complete_date,
                    ),
                ],
            ),
            NavSection(
                name="Initial statement",
                pages=[
                    NavPage(
                        url=reverse(
                            "audits:edit-statement-pages", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_statement_pages_complete_date,
                    ),
                    NavPage(
                        url=reverse(
                            "audits:edit-statement-overview", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_statement_overview_complete_date,
                        subpages=[
                            NavPage(
                                url=reverse(
                                    "audits:edit-statement-website",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_website_complete_date,
                            ),
                            NavPage(
                                url=reverse(
                                    "audits:edit-statement-compliance",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_compliance_complete_date,
                            ),
                            NavPage(
                                url=reverse(
                                    "audits:edit-statement-non-accessible",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_non_accessible_complete_date,
                            ),
                            NavPage(
                                url=reverse(
                                    "audits:edit-statement-preparation",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_preparation_complete_date,
                            ),
                            NavPage(
                                url=reverse(
                                    "audits:edit-statement-feedback",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_feedback_complete_date,
                            ),
                            NavPage(
                                url=reverse(
                                    "audits:edit-statement-custom",
                                    kwargs=kwargs_audit_pk,
                                ),
                                complete=case.audit.audit_statement_custom_complete_date,
                            ),
                        ],
                    ),
                    NavPage(
                        url=reverse(
                            "audits:edit-initial-disproportionate-burden",
                            kwargs=kwargs_audit_pk,
                        ),
                        complete=case.audit.initial_disproportionate_burden_complete_date,
                    ),
                    NavPage(
                        url=reverse(
                            "audits:edit-statement-decision", kwargs=kwargs_audit_pk
                        ),
                        complete=case.audit.audit_statement_decision_complete_date,
                    ),
                    NavPage(
                        url=reverse(
                            "audits:edit-audit-statement-summary",
                            kwargs=kwargs_audit_pk,
                        ),
                        complete=case.audit.audit_statement_summary_complete_date,
                    ),
                ],
            ),
        ]
    return [
        NavSection(
            name="Case details",
            pages=[
                NavPage(
                    url=reverse("cases:edit-case-metadata", kwargs=kwargs_case_pk),
                    complete=case.case_details_complete_date,
                )
            ],
        ),
    ] + audit_nav_sections


def build_closing_the_case_nav_sections(case: Case) -> List[NavSection]:
    """Return closing the case sections for navigation details elements"""
    kwargs_case_pk: Dict[str, int] = {"pk": case.id}
    return [
        NavSection(
            name="Closing the case",
            pages=[
                NavPage(
                    url=reverse("cases:edit-review-changes", kwargs=kwargs_case_pk),
                    complete=case.review_changes_complete_date,
                ),
                NavPage(
                    url=reverse(
                        "cases:edit-enforcement-recommendation", kwargs=kwargs_case_pk
                    ),
                    complete=case.enforcement_recommendation_complete_date,
                ),
                NavPage(
                    url=reverse("cases:edit-case-close", kwargs=kwargs_case_pk),
                    complete=case.case_close_complete_date,
                ),
            ],
        ),
    ]
