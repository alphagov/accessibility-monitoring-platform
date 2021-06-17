""" Common utility functions """
from datetime import date, datetime
import re
import csv
import pytz
from typing import (
    Any,
    Dict,
    List,
    Tuple,
)

from django.db.models import QuerySet
from django.http import HttpResponse
from django.http.request import QueryDict

from .typing import IntOrNone, StringOrNone


def download_as_csv(
    queryset: QuerySet, field_names: List[str], filename: str = "download.csv"
) -> HttpResponse:
    """ Given a queryset and a list of field names, download the data in csv format """
    response: Any = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"

    writer: Any = csv.writer(response)
    writer.writerow(field_names)

    output: List[List[str]] = []
    for item in queryset:
        output.append([getattr(item, field_name) for field_name in field_names])

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
        object_id = int(key_names[0].replace(button_name_prefix, ""))
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


def convert_date_to_datetime(input_date: date) -> datetime:
    """
    Python dates are not timezone-aware. This function converts a date into a timezone-aware
    datetime with a time of midnight UTC
    """
    return datetime(
        year=input_date.year,
        month=input_date.month,
        day=input_date.day,
        tzinfo=pytz.UTC,
    )
