""" Common utility functions """
from datetime import date, datetime, timedelta
import re
import csv
import pytz
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Union
)

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import HttpResponse
from django.http.request import QueryDict
from django.db.models import Q
from .typing import IntOrNone, StringOrNone

CONTACT_FIELDS = ["contact_email", "contact_notes"]


def download_as_csv(
    queryset: QuerySet,
    field_names: List[str],
    filename: str = "download.csv",
    include_contact: bool = False,
) -> HttpResponse:
    """Given a queryset and a list of field names, download the data in csv format"""
    response: Any = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"

    writer: Any = csv.writer(response)
    if include_contact:
        writer.writerow(field_names + CONTACT_FIELDS)
    else:
        writer.writerow(field_names)

    output: List[List[str]] = []
    for item in queryset:
        row = []
        for field_name in field_names:
            item_attr = getattr(item, field_name)
            if hasattr(item_attr, "all"):
                value = ",".join(
                    [str(related_item) for related_item in item_attr.all()]
                )
            else:
                value = item_attr
            row.append(value)

        if include_contact:
            contacts = list(item.contact_set.filter(is_archived=False))
            if contacts:
                row.append(contacts[0].detail)
                row.append(contacts[0].notes)

        output.append(row)

    writer.writerows(output)

    return response


def extract_domain_from_url(url):
    domain_match = re.search("https?://([A-Za-z_0-9.-]+).*", url)
    return domain_match.group(1) if domain_match else ""


def get_id_from_button_name(button_name_prefix: str, querydict: QueryDict) -> IntOrNone:
    """
    Given a button name in the form: prefix_[id] extract and return the id value.
    """
    key_names: Dict[str] = [
        key for key in querydict.keys() if key.startswith(button_name_prefix)
    ]
    object_id: IntOrNone = None
    if len(key_names) == 1:
        id_string: str = key_names[0].replace(button_name_prefix, "")
        object_id: IntOrNone = int(id_string) if id_string.isdigit() else None
    return object_id


def build_filters(
    cleaned_data: Dict, field_and_filter_names: List[Tuple[str, str]]
) -> Dict[str, Any]:
    """
    Given the form cleaned_data, work through a list of field and filter names
    to build up a dictionary of filters to apply in a queryset.
    """
    filters: Dict[str, Any] = {}
    for field_name, filter_name in field_and_filter_names:
        value: StringOrNone = cleaned_data.get(field_name)
        if value:
            filters[filter_name] = value
    return filters


def convert_date_to_datetime(
    input_date: date, hour: int = 0, minute: int = 0, second: int = 0
) -> datetime:
    """
    Python dates are not timezone-aware. This function converts a date into a timezone-aware
    datetime with a time of midnight UTC
    """
    return datetime(
        year=input_date.year,
        month=input_date.month,
        day=input_date.day,
        hour=hour,
        minute=minute,
        second=second,
        tzinfo=pytz.UTC,
    )


def filter_by_status(query_set: QuerySet, status: str) -> Union[QuerySet, None]:
    """Takes a QuerySet and a string describing a status. Returns the rows
    of the QuerySet that match that status.

    Args:
        query_set (QuerySet): A Case QuerySet object
        status (str): a string describing the status

    Returns:
        [QuerySet]: Filtered QuerySet
        [None]: if status doesn't exist
    """

    if status == "unassigned_cases":
        return query_set.filter(
            auditor__isnull=True,
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        )

    if status == "unassigned_qa_cases":
        return query_set.filter(
            reviewer__isnull=True,
            report_review_status="ready-to-review",
            report_approved_status="no",
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        )

    if status == "new_case":
        return query_set.filter(
            auditor__isnull=False,
            contact__case__isnull=True,
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        )

    if status == "test_in_progress":
        return query_set.filter(
            Q(test_status="in-progress") | Q(test_status="not-started"),
            auditor__isnull=False,
            contact__case__isnull=False,
            report_sent_date__isnull=True,
            report_acknowledged_date__isnull=True,
            week_12_followup_date__isnull=True,
            compliance_email_sent_date__isnull=True,
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        )

    if status == "report_in_progress":
        return query_set.filter(
            auditor__isnull=False,
            contact__case__isnull=False,
            test_status="complete",
            report_sent_date__isnull=True,
            report_acknowledged_date__isnull=True,
            week_12_followup_date__isnull=True,
            compliance_email_sent_date__isnull=True,
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        )

    if status == "awaiting_response_to_report":
        return query_set.filter(
            report_sent_date__isnull=False,
            report_acknowledged_date__isnull=True,
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        ).order_by("report_sent_date")

    if status == "twelve_week_review_due":
        return query_set.filter(
            report_acknowledged_date__isnull=False,
            compliance_email_sent_date__isnull=True,
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        ).order_by("week_12_followup_date")

    if status == "update_for_enforcement_bodies_due":
        return query_set.filter(
            compliance_email_sent_date__isnull=False,
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        )

    if status == "recently_completed":
        return query_set.filter(
            is_case_completed=True,
            completed__gte=datetime.now() - timedelta(30),
            is_archived=False,
            is_public_sector_body=True
        )

    if status == "qa_cases":
        return query_set.filter(
            reviewer_id__isnull=False,
            report_review_status="ready-to-review",
            report_approved_status="no",
            is_archived=False,
            is_public_sector_body=True
        )

    return None


def validate_url(url):
    """
    Validate URL string entered by user
    """

    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValidationError("URL must start with http:// or https://")
