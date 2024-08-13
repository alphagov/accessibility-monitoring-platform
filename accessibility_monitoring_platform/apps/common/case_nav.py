"""Case navigation sections defined and added to context"""

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

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
                case_id: int = self.kwargs.get("case_id")
                case: Case = Case.objects.get(id=case_id)
            if case is not None:
                context["case"] = case

        if case is not None:
            context["case_nav_sections"] = build_case_nav_sections(case=case)
            context["closing_the_case_nav_sections"] = (
                build_closing_the_case_nav_sections(case=case)
            )
            context["correspondence_nav_sections"] = build_correspondence_nav_sections(
                case=case
            )

        return context


class NavPage:
    url: str
    disabled: bool = False
    complete: bool = False
    subpages: Optional[List["NavPage"]] = None

    def __init__(
        self,
        url: str,
        disabled: bool = False,
        complete: Optional[date] = None,
        subpages: Optional[List["NavPage"]] = None,
    ):
        self.url = url
        self.disabled = disabled
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


def build_correspondence_nav_sections(case: Case) -> List[NavSection]:
    """Return correspondence sections for navigation details elements"""
    kwargs_case_pk: Dict[str, int] = {"pk": case.id}
    return [
        NavSection(
            name="Contact details",
            pages=[
                NavPage(
                    url=reverse(
                        "cases:edit-contact-details-list", kwargs=kwargs_case_pk
                    ),
                    complete=case.contact_details_complete_date,
                    subpages=[
                        NavPage(
                            url=reverse(
                                "cases:edit-contact-create", kwargs={"case_id": case.id}
                            ),
                        ),
                    ],
                ),
                NavPage(
                    url=reverse(
                        "cases:edit-request-contact-details", kwargs=kwargs_case_pk
                    ),
                    disabled=not case.enable_correspondence_process,
                    complete=case.request_contact_details_complete_date,
                ),
                NavPage(
                    url=reverse(
                        "cases:edit-one-week-contact-details", kwargs=kwargs_case_pk
                    ),
                    disabled=not case.enable_correspondence_process,
                    complete=case.one_week_contact_details_complete_date,
                ),
                NavPage(
                    url=reverse(
                        "cases:edit-four-week-contact-details", kwargs=kwargs_case_pk
                    ),
                    disabled=not case.enable_correspondence_process,
                    complete=case.four_week_contact_details_complete_date,
                ),
                NavPage(
                    url=reverse("cases:edit-no-psb-response", kwargs=kwargs_case_pk),
                    disabled=not case.enable_correspondence_process,
                    complete=case.no_psb_contact_complete_date,
                ),
            ],
        ),
        NavSection(
            name="Report correspondence",
            pages=[
                NavPage(
                    url=reverse("cases:edit-report-sent-on", kwargs=kwargs_case_pk),
                    complete=case.report_sent_on_complete_date,
                ),
                NavPage(
                    url=reverse(
                        "cases:edit-report-one-week-followup", kwargs=kwargs_case_pk
                    ),
                    complete=case.one_week_followup_complete_date,
                ),
                NavPage(
                    url=reverse(
                        "cases:edit-report-four-week-followup", kwargs=kwargs_case_pk
                    ),
                    complete=case.four_week_followup_complete_date,
                ),
                NavPage(
                    url=reverse(
                        "cases:edit-report-acknowledged", kwargs=kwargs_case_pk
                    ),
                    complete=case.report_acknowledged_complete_date,
                ),
            ],
        ),
        NavSection(
            name="12-week correspondence",
            pages=[
                NavPage(
                    url=reverse(
                        "cases:edit-12-week-update-requested", kwargs=kwargs_case_pk
                    ),
                    complete=case.twelve_week_update_requested_complete_date,
                ),
                NavPage(
                    url=reverse(
                        "cases:edit-12-week-one-week-followup-final",
                        kwargs=kwargs_case_pk,
                    ),
                    complete=case.one_week_followup_final_complete_date,
                ),
                NavPage(
                    url=reverse(
                        "cases:edit-12-week-update-request-ack", kwargs=kwargs_case_pk
                    ),
                    complete=case.twelve_week_update_request_ack_complete_date,
                ),
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
