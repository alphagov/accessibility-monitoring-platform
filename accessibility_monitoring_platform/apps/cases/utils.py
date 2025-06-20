"""
Utility functions for cases app
"""

import copy
from typing import Any, ClassVar

from django.db.models import Case as DjangoCase
from django.db.models import Q, QuerySet, When

from ..common.utils import build_filters
from ..simplified.models import SimplifiedCase
from .models import BaseCase, Sort

CASE_FIELD_AND_FILTER_NAMES: list[tuple[str, str]] = [
    ("auditor", "auditor_id"),
    ("reviewer", "reviewer_id"),
    ("status", "status"),
    ("sector", "sector_id"),
    ("subcategory", "subcategory_id"),
    ("test_type", "test_type"),
]


def filter_cases(form) -> QuerySet[BaseCase] | QuerySet[SimplifiedCase]:
    """Return a queryset of Cases filtered by the values in CaseSearchForm"""
    filters: dict = {}
    search_query = Q()
    sort_by: str = Sort.NEWEST

    if hasattr(form, "cleaned_data"):
        field_and_filter_names: list[tuple[str, str]] = copy.copy(
            CASE_FIELD_AND_FILTER_NAMES
        )
        if "date_type" in form.cleaned_data:
            date_range_field: str = form.cleaned_data["date_type"]
            field_and_filter_names.append(("date_start", f"{date_range_field}__gte"))
            field_and_filter_names.append(("date_end", f"{date_range_field}__lte"))
        filters: dict[str, Any] = build_filters(
            cleaned_data=form.cleaned_data,
            field_and_filter_names=field_and_filter_names,
        )
        sort_by: str = form.cleaned_data.get("sort_by", Sort.NEWEST)
        if form.cleaned_data.get("case_search"):
            search: str = form.cleaned_data["case_search"]
            if (
                search.isdigit()
            ):  # if its just a number, it presumes its an ID and returns that case
                search_query = Q(case_number=search)
            else:
                search_query = (
                    Q(  # pylint: disable=unsupported-binary-operation
                        organisation_name__icontains=search
                    )
                    | Q(home_page_url__icontains=search)
                    | Q(domain__icontains=search)
                    | Q(psb_location__icontains=search)
                    | Q(sector__name__icontains=search)
                    | Q(parental_organisation_name__icontains=search)
                    | Q(website_name__icontains=search)
                    | Q(subcategory__name__icontains=search)
                    | Q(case_identifier__icontains=search)
                    | Q(mobilecase__app_name__icontains=search)
                )
        for filter_name in [
            "is_complaint",
            "enforcement_body",
            "recommendation_for_enforcement",
        ]:
            filter_value: str = form.cleaned_data.get(filter_name, "")
            if filter_value != "":
                filters[filter_name] = filter_value
    else:
        filters["test_type"] = BaseCase.TestType.SIMPLIFIED

    if str(filters.get("status", "")) == BaseCase.Status.READY_TO_QA:
        filters["test_type"] = BaseCase.TestType.SIMPLIFIED
        filters["status"] = BaseCase.Status.QA_IN_PROGRESS
        filters["simplifiedcase__qa_status"] = SimplifiedCase.QAStatus.UNASSIGNED

    # Auditor and reviewer may be filtered by unassigned
    if "auditor_id" in filters and filters["auditor_id"] == "none":
        filters["auditor_id"] = None
    if "reviewer_id" in filters and filters["reviewer_id"] == "none":
        filters["reviewer_id"] = None

    if "recommendation_for_enforcement" in filters:
        search_model: ClassVar[SimplifiedCase] = SimplifiedCase
    else:
        search_model: ClassVar[BaseCase] = BaseCase

    if not sort_by:
        return (
            search_model.objects.filter(search_query, **filters)
            .annotate(
                position_unassigned_first=DjangoCase(
                    When(status=BaseCase.Status.UNASSIGNED, then=0),
                    default=1,
                )
            )
            .order_by("position_unassigned_first", "-id")
            .select_related("auditor", "reviewer")
        )
    return (
        search_model.objects.filter(search_query, **filters)
        .order_by(sort_by)
        .select_related("auditor", "reviewer")
    )
