"""
Utility functions for cases app
"""

import copy
import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any

from django.contrib.auth.models import User
from django.db.models import Case as DjangoCase
from django.db.models import Q, QuerySet, When

from ..common.utils import build_filters, extract_domain_from_url
from ..detailed.models import DetailedCase, DetailedCaseHistory
from ..simplified.models import SimplifiedCase
from .models import CASE_STATUS_UNASSIGNED, BaseCase, Sort

CASE_FIELD_AND_FILTER_NAMES: list[tuple[str, str]] = [
    ("auditor", "auditor_id"),
    ("reviewer", "reviewer_id"),
    ("status", "status"),
    ("sector", "sector_id"),
    ("subcategory", "subcategory_id"),
    ("test_type", "test_type"),
    ("is_complaint", "is_complaint"),
    ("enforcement_body", "enforcement_body"),
    ("recommendation_for_enforcement", "recommendation_for_enforcement"),
]

logger = logging.getLogger(__name__)


def filter_cases(form) -> QuerySet[BaseCase]:
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
            if form.cleaned_data.get("date_start") is not None:
                field_and_filter_names.append(
                    ("date_start", f"{date_range_field}__gte")
                )
            if form.cleaned_data.get("date_end") is not None:
                field_and_filter_names.append(("date_end", f"{date_range_field}__lte"))
        filters: dict[str, Any] = build_filters(
            cleaned_data=form.cleaned_data,
            field_and_filter_names=field_and_filter_names,
        )
        sort_by: str = form.cleaned_data.get("sort_by", Sort.NEWEST)
        if form.cleaned_data.get("case_search"):
            search: str = form.cleaned_data["case_search"]
            search_query = (
                Q(organisation_name__icontains=search)
                | Q(home_page_url__icontains=search)
                | Q(psb_location__icontains=search)
                | Q(sector__name__icontains=search)
                | Q(parental_organisation_name__icontains=search)
                | Q(website_name__icontains=search)
                | Q(subcategory__name__icontains=search)
                | Q(case_identifier__icontains=search)
                | Q(mobilecase__app_name__icontains=search)
                | Q(mobilecase__app_store_url__icontains=search)
            )

    if str(filters.get("status", "")) == SimplifiedCase.Status.READY_TO_QA:
        filters["test_type"] = BaseCase.TestType.SIMPLIFIED
        filters["status"] = SimplifiedCase.Status.QA_IN_PROGRESS
        filters["simplifiedcase__qa_status"] = SimplifiedCase.QAStatus.UNASSIGNED

    # Auditor and reviewer may be filtered by unassigned
    if "auditor_id" in filters and filters["auditor_id"] == "none":
        filters["auditor_id"] = None
    if "reviewer_id" in filters and filters["reviewer_id"] == "none":
        filters["reviewer_id"] = None

    if not sort_by:
        return (
            BaseCase.objects.filter(search_query, **filters)
            .annotate(
                position_unassigned_first=DjangoCase(
                    When(status=CASE_STATUS_UNASSIGNED.value, then=0),
                    default=1,
                )
            )
            .order_by("position_unassigned_first", "-id")
            .select_related("auditor", "reviewer")
        )
    return (
        BaseCase.objects.filter(search_query, **filters)
        .order_by(sort_by)
        .select_related("auditor", "reviewer")
    )


def find_duplicate_cases(url: str, organisation_name: str = "") -> QuerySet[BaseCase]:
    """Look for cases with matching domain or organisation name"""
    domain: str = extract_domain_from_url(url)
    if organisation_name:
        return BaseCase.objects.filter(
            Q(organisation_name__icontains=organisation_name) | Q(domain=domain)
        )
    return BaseCase.objects.filter(domain=domain)


COMMENT_FULLNAME_TO_USERNAME: dict[str, str] = {
    "amy.wallis": "amy.wallis@digital.cabinet-office.gov.uk",
    "Andrew Hick": "andrew.hick@digital.cabinet-office.gov.uk",
    "ChrisH": "chris.heathcote@digital.cabinet-office.gov.uk",
    "Eu-Hyung Han": "eu-hyung.han@digital.cabinet-office.gov.uk",
    "Jessica Eley": "jessica.eley@digital.cabinet-office.gov.uk",
    "katherine.badger": "katherine.badger@digital.cabinet-office.gov.uk",
    "Keeley Robertson": "keeley.talbot@digital.cabinet-office.gov.uk",
    "Kelly Clarkson": "kelly.clarkson@digital.cabinet-office.gov.uk",
    "nesha.russo": "nesha.russo@digital.cabinet-office.gov.uk",
    "Nicole Tinti": "nicole.tinti@digital.cabinet-office.gov.uk",
}
TRELLO_COMMENT_LABEL: str = "Imported from Trello"


def import_trello_comments(csv_data: str) -> None:
    try:
        comment_fullname_to_user: dict[str, User] = {
            comment_fullname: User.objects.get(username=username)
            for comment_fullname, username in COMMENT_FULLNAME_TO_USERNAME.items()
        }
    except User.DoesNotExist:  # Automated tests
        return
    DetailedCaseHistory.objects.filter(label=TRELLO_COMMENT_LABEL).delete()
    reader: Any = csv.DictReader(io.StringIO(csv_data))
    for row in reader:
        case_no: str = row["case_no"]
        if case_no == "":
            continue
        if row["case_no"].startswith("D"):
            case_identifier: str = f"#D-{case_no[1:]}"
            try:
                detailed_case: DetailedCase = DetailedCase.objects.get(
                    case_identifier=case_identifier
                )
                detailed_case_history: DetailedCaseHistory = (
                    DetailedCaseHistory.objects.create(
                        detailed_case=detailed_case,
                        event_type=DetailedCaseHistory.EventType.NOTE,
                        value=row["comment_text"],
                        label=TRELLO_COMMENT_LABEL,
                        created_by=comment_fullname_to_user[row["comment_fullname"]],
                    )
                )
                comment_time: datetime = datetime.strptime(
                    row["comment_date"], "%Y-%m-%dT%H:%M:%S.%fZ"
                ).replace(tzinfo=timezone.utc)
                detailed_case_history.created = comment_time
                detailed_case_history.updated = comment_time
                detailed_case_history.save()
            except DetailedCase.DoesNotExist:
                logger.warning("DetailedCase not found: %s", case_identifier)
