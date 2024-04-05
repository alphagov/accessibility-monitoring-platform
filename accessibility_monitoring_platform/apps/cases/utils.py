"""
Utility functions for cases app
"""

import copy
from dataclasses import dataclass
from datetime import date
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from django import forms
from django.contrib.auth.models import User
from django.db.models import Case as DjangoCase
from django.db.models import Q, QuerySet, When
from django.http.request import QueryDict
from django.urls import reverse

from ..audits.models import Retest
from ..common.form_extract_utils import (  # FieldLabelAndValue,
    extract_form_labels_and_values,
)
from ..common.utils import build_filters
from ..common.view_section_utils import ViewSection, build_view_section  # ViewSubTable
from .forms import CaseDetailUpdateForm
from .models import (
    COMPLIANCE_FIELDS,
    Case,
    CaseEvent,
    CaseStatus,
    Complaint,
    EqualityBodyCorrespondence,
    Sort,
)

CASE_FIELD_AND_FILTER_NAMES: List[Tuple[str, str]] = [
    ("auditor", "auditor_id"),
    ("reviewer", "reviewer_id"),
    ("status", "status"),
    ("sector", "sector_id"),
    ("subcategory", "subcategory_id"),
]


@dataclass
class PostCaseAlert:
    """Data to use in html table row of post case alerts page"""

    date: date
    case: Case
    description: str
    absolute_url: str
    absolute_url_label: str


def get_case_view_sections(case: Case) -> List[ViewSection]:
    """Get sections for case view"""
    get_case_rows: Callable = partial(extract_form_labels_and_values, instance=case)
    case_pk: Dict[str, int] = {"pk": case.id}
    return [
        build_view_section(
            name="Case details",
            edit_url=reverse("cases:edit-case-details", kwargs=case_pk),
            edit_url_id="edit-case-details",
            complete_date=case.case_details_complete_date,
            display_fields=get_case_rows(form=CaseDetailUpdateForm()),
        ),
    ]


def get_sent_date(
    form: forms.ModelForm, case_from_db: Case, sent_date_name: str
) -> Union[date, None]:
    """
    Work out what value to save in a sent date field on the case.
    If there is a new value in the form, don't replace an existing date on the database.
    If there is a new value in the form and no date on the database then use the date from the form.
    If there is no value in the form (i.e. the checkbox is unchecked), set the date on the database to None.
    """
    date_on_form: Optional[date] = form.cleaned_data.get(sent_date_name)
    if date_on_form is None:
        return None
    date_on_db: date = getattr(case_from_db, sent_date_name)
    return date_on_db if date_on_db else date_on_form


def filter_cases(form) -> QuerySet[Case]:  # noqa: C901
    """Return a queryset of Cases filtered by the values in CaseSearchForm"""
    filters: Dict = {}
    search_query = Q()
    sort_by: str = Sort.NEWEST

    if hasattr(form, "cleaned_data"):
        field_and_filter_names: List[Tuple[str, str]] = copy.copy(
            CASE_FIELD_AND_FILTER_NAMES
        )
        if "date_type" in form.cleaned_data:
            date_range_field: str = form.cleaned_data["date_type"]
            field_and_filter_names.append(("date_start", f"{date_range_field}__gte"))
            field_and_filter_names.append(("date_end", f"{date_range_field}__lte"))
        filters: Dict[str, Any] = build_filters(
            cleaned_data=form.cleaned_data,
            field_and_filter_names=field_and_filter_names,
        )
        sort_by: str = form.cleaned_data.get("sort_by", Sort.NEWEST)
        if form.cleaned_data.get("case_search"):
            search: str = form.cleaned_data["case_search"]
            if (
                search.isdigit()
            ):  # if its just a number, it presumes its an ID and returns that case
                search_query = Q(id=search)
            else:
                search_query = (
                    Q(  # pylint: disable=unsupported-binary-operation
                        organisation_name__icontains=search
                    )
                    | Q(home_page_url__icontains=search)
                    | Q(psb_location__icontains=search)
                    | Q(sector__name__icontains=search)
                    | Q(parental_organisation_name__icontains=search)
                    | Q(website_name__icontains=search)
                    | Q(subcategory__name__icontains=search)
                )
        for filter_name in ["is_complaint", "enforcement_body"]:
            filter_value: str = form.cleaned_data.get(filter_name, Complaint.ALL)
            if filter_value != Complaint.ALL:
                filters[filter_name] = filter_value

    if str(filters.get("status", "")) == CaseStatus.Status.READY_TO_QA:
        filters["qa_status"] = CaseStatus.Status.READY_TO_QA
        del filters["status"]

    if "status" in filters:
        filters["status__status"] = filters["status"]
        del filters["status"]

    # Auditor and reviewer may be filtered by unassigned
    if "auditor_id" in filters and filters["auditor_id"] == "none":
        filters["auditor_id"] = None
    if "reviewer_id" in filters and filters["reviewer_id"] == "none":
        filters["reviewer_id"] = None

    if not sort_by:
        return (
            Case.objects.filter(search_query, **filters)
            .annotate(
                position_unassigned_first=DjangoCase(
                    When(status__status=CaseStatus.Status.UNASSIGNED, then=0), default=1
                )
            )
            .order_by("position_unassigned_first", "-id")
            .select_related("auditor", "reviewer")
        )
    return (
        Case.objects.filter(search_query, **filters)
        .order_by(sort_by)
        .select_related("auditor", "reviewer")
    )


def replace_search_key_with_case_search(request_get: QueryDict) -> Dict[str, str]:
    """Convert QueryDict to dictionary and replace key 'search' with 'case_search'."""
    search_args: Dict[str, str] = {key: value for key, value in request_get.items()}
    if "search" in search_args:
        search_args["case_search"] = search_args.pop("search")
    return search_args


def record_case_event(
    user: User, new_case: Case, old_case: Optional[Case] = None
) -> None:
    """Create a case event based on the changes between the old and new cases"""
    if old_case is None:
        CaseEvent.objects.create(
            case=new_case, done_by=user, event_type=CaseEvent.EventType.CREATE
        )
        return
    if old_case.auditor != new_case.auditor:
        old_user_name: str = (
            old_case.auditor.get_full_name() if old_case.auditor is not None else "none"
        )
        new_user_name: str = (
            new_case.auditor.get_full_name() if new_case.auditor is not None else "none"
        )
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.AUDITOR,
            message=f"Auditor changed from {old_user_name} to {new_user_name}",
        )
    if old_case.audit is None and new_case.audit is not None:
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.CREATE_AUDIT,
            message="Start of test",
        )
    if old_case.report_review_status != new_case.report_review_status:
        old_status: str = old_case.get_report_review_status_display()
        new_status: str = new_case.get_report_review_status_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.READY_FOR_QA,
            message=f"Report ready to be reviewed changed from '{old_status}' to '{new_status}'",
        )
    if old_case.reviewer != new_case.reviewer:
        old_user_name: str = (
            old_case.reviewer.get_full_name()
            if old_case.reviewer is not None
            else "none"
        )
        new_user_name: str = (
            new_case.reviewer.get_full_name()
            if new_case.reviewer is not None
            else "none"
        )
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.QA_AUDITOR,
            message=f"QA auditor changed from {old_user_name} to {new_user_name}",
        )
    if old_case.report_approved_status != new_case.report_approved_status:
        old_status: str = old_case.get_report_approved_status_display()
        new_status: str = new_case.get_report_approved_status_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.APPROVE_REPORT,
            message=f"Report approved changed from '{old_status}' to '{new_status}'",
        )
    if old_case.is_ready_for_final_decision != new_case.is_ready_for_final_decision:
        old_status: str = old_case.get_is_ready_for_final_decision_display()
        new_status: str = new_case.get_is_ready_for_final_decision_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.READY_FOR_FINAL_DECISION,
            message=f"Case ready for final decision changed from '{old_status}' to '{new_status}'",
        )
    if old_case.case_completed != new_case.case_completed:
        old_status: str = old_case.get_case_completed_display()
        new_status: str = new_case.get_case_completed_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.CASE_COMPLETED,
            message=f"Case completed changed from '{old_status}' to '{new_status}'",
        )


def build_edit_link_html(case: Case, url_name: str) -> str:
    """Return html of edit link for case"""
    case_pk: Dict[str, int] = {"pk": case.id}
    edit_url: str = reverse(url_name, kwargs=case_pk)
    return (
        f"<a href='{edit_url}' class='govuk-link govuk-link--no-visited-state'>Edit</a>"
    )


def create_case_and_compliance(**kwargs):
    """Create case and populate compliance fields from arbitrary arguments"""
    compliance_kwargs: Dict[str, Any] = {
        key: value for key, value in kwargs.items() if key in COMPLIANCE_FIELDS
    }
    non_compliance_args: Dict[str, Any] = {
        key: value for key, value in kwargs.items() if key not in COMPLIANCE_FIELDS
    }
    case: Case = Case.objects.create(**non_compliance_args)
    if compliance_kwargs:
        for key, value in compliance_kwargs.items():
            setattr(case.compliance, key, value)
        case.compliance.save()
        case.save()
    return case


def get_post_case_alerts_count(user: User) -> int:
    """
    Return the number of unresolved equality body correspondence entries
    and incomplete equality body retests for user.
    """
    if user.id:
        return (
            EqualityBodyCorrespondence.objects.filter(
                case__auditor=user, status=EqualityBodyCorrespondence.Status.UNRESOLVED
            ).count()
            + Retest.objects.filter(
                is_deleted=False,
                case__auditor=user,
                retest_compliance_state=Retest.Compliance.NOT_KNOWN,
                id_within_case__gt=0,
            ).count()
        )
    return 0


def get_post_case_alerts(user: User) -> List[PostCaseAlert]:
    """
    Return sorted list of unresolved equality body correspondence entries and
    incomplete equality body retests for a user.
    """
    post_case_alerts: List[PostCaseAlert] = []

    equality_body_correspondences: QuerySet[
        EqualityBodyCorrespondence
    ] = EqualityBodyCorrespondence.objects.filter(
        case__auditor=user,
        status=EqualityBodyCorrespondence.Status.UNRESOLVED,
    )

    for equality_body_correspondence in equality_body_correspondences:
        post_case_alerts.append(
            PostCaseAlert(
                date=equality_body_correspondence.created.date(),
                case=equality_body_correspondence.case,
                description="Unresolved correspondence",
                absolute_url=f"{equality_body_correspondence.get_absolute_url()}?view=unresolved",
                absolute_url_label="View correspondence",
            )
        )

    retests: QuerySet[Retest] = Retest.objects.filter(
        is_deleted=False,
        case__auditor=user,
        retest_compliance_state=Retest.Compliance.NOT_KNOWN,
        id_within_case__gt=0,
    )

    for retest in retests:
        post_case_alerts.append(
            PostCaseAlert(
                date=retest.date_of_retest,
                case=retest.case,
                description="Incomplete retest",
                absolute_url=retest.get_absolute_url(),
                absolute_url_label="View retest",
            )
        )
    return sorted(post_case_alerts, key=lambda alert: alert.date, reverse=True)
