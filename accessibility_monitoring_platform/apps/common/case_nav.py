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
            elif "pk" in self.kwargs:
                case: Case = get_object_or_404(Case, id=self.kwargs.get("pk"))
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
    ]


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
