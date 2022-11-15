""" Common utility functions """
from datetime import date, datetime, timedelta

import re
import calendar
import csv
import json
from typing import (
    Any,
    Dict,
    List,
    Match,
    Optional,
    Tuple,
    Type,
    Union,
)
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.db.models.fields.reverse_related import ManyToOneRel
from django.http import HttpResponse
from django.http.request import QueryDict
from django.utils import timezone

from django_otp.plugins.otp_email.models import EmailDevice

from .models import Event, Platform, EVENT_TYPE_MODEL_CREATE, ChangeToPlatform

CONTACT_FIELDS = ["contact_email", "contact_notes"]
GRAPH_HEIGHT: int = 250
CHART_HEIGHT_EXTRA: int = 50
CHART_WIDTH_EXTRA: int = 150
X_AXIS_STEP: int = 50
X_AXIS_TICK_HEIGHT: int = 10
X_AXIS_LABEL_1_Y_OFFSET: int = 25
X_AXIS_LABEL_2_Y_OFFSET: int = 45
Y_AXIS_LABELS_250: List[Dict[str, Union[str, int]]] = [
    {"label": "250", "y": 0},
    {"label": "200", "y": 50},
    {"label": "150", "y": 100},
    {"label": "100", "y": 150},
    {"label": "50", "y": 200},
    {"label": "0", "y": 250},
]
Y_AXIS_LABELS_100: List[Dict[str, Union[str, int]]] = [
    {"label": "100", "y": 0},
    {"label": "50", "y": 125},
    {"label": "0", "y": 250},
]
MULTIPLIER_100_TO_250: float = 250 / 100


def get_field_names_for_export(model: Type[models.Model]) -> List[str]:
    """
    Returns a list of names of all the fields in a model.
    Exclude those representing reverse relationships.
    """
    return [
        field.name
        for field in model._meta.get_fields()  # pylint: disable=protected-access
        if not isinstance(field, ManyToOneRel)
    ]


def download_as_csv(
    queryset: QuerySet[Any],
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
        row: List[str] = []
        for field_name in field_names:
            item_attr: Any = getattr(item, field_name)
            if hasattr(item_attr, "all"):
                value: str = ",".join(
                    [str(related_item) for related_item in item_attr.all()]
                )
            else:
                value: str = str(item_attr)
            row.append(value)

        if include_contact:
            contacts: List[Any] = list(item.contact_set.filter(is_deleted=False))  # type: ignore
            if contacts:
                row.append(contacts[0].email)
                row.append(contacts[0].notes)

        output.append(row)

    writer.writerows(output)

    return response


def extract_domain_from_url(url: str) -> str:
    """Extract and return domain string from url string"""
    domain_match: Union[Match[str], None] = re.search(
        "https?://([A-Za-z_0-9.-]+).*", url
    )
    return domain_match.group(1) if domain_match else ""


def get_id_from_button_name(
    button_name_prefix: str, querydict: QueryDict
) -> Optional[int]:
    """
    Given a button name in the form: prefix_[id] extract and return the id value.
    """
    key_names: List[str] = [
        key for key in querydict.keys() if key.startswith(button_name_prefix)
    ]
    object_id: Optional[int] = None
    if len(key_names) == 1:
        id_string: str = key_names[0].replace(button_name_prefix, "")
        object_id: Optional[int] = int(id_string) if id_string.isdigit() else None
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
        value: Optional[str] = cleaned_data.get(field_name)
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
        tzinfo=ZoneInfo("UTC"),
    )


def validate_url(url: str) -> None:
    """
    Validate URL string entered by user
    """

    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValidationError("URL must start with http:// or https://")


def get_platform_settings() -> Platform:
    """Return the platform-wide settings"""
    return Platform.objects.get(pk=1)


def get_recent_changes_to_platform() -> QuerySet[ChangeToPlatform]:
    """Find platform changes made in last 24 hours"""
    twenty_four_hours_ago: datetime = timezone.now() - timedelta(hours=24)
    return ChangeToPlatform.objects.filter(created__gte=twenty_four_hours_ago)


def record_model_update_event(user: User, model_object: models.Model) -> None:
    """Record model update event"""
    value: Dict[str, str] = {}
    old_model = model_object.__class__.objects.get(pk=model_object.id)  # type: ignore
    value["old"] = serializers.serialize("json", [old_model])
    value["new"] = serializers.serialize("json", [model_object])
    Event.objects.create(created_by=user, parent=model_object, value=json.dumps(value))


def record_model_create_event(user: User, model_object: models.Model) -> None:
    """Record model create event"""
    value: Dict[str, str] = {"new": serializers.serialize("json", [model_object])}
    Event.objects.create(
        created_by=user,
        parent=model_object,
        type=EVENT_TYPE_MODEL_CREATE,
        value=json.dumps(value),
    )


def list_to_dictionary_of_lists(
    items: List[Any], group_by_attr: str
) -> Dict[Any, List[Any]]:
    """
    Group a list of items by an attribute of those items and return a dictionary
    with that attribute as the key and the value being a list of items matching the attribute.

    """
    dict_of_lists_of_items: Dict[Any, List[Any]] = {}
    for item in items:
        dict_of_lists_of_items.setdefault(getattr(item, group_by_attr), []).append(item)
    return dict_of_lists_of_items


def amp_format_date(date_to_format: date) -> str:
    """Format date according to GDS style guide"""
    return f"{date_to_format:%-d %B %Y}" if date_to_format else ""


def amp_format_time(datetime_to_format: datetime) -> str:
    """Format time according to GDS style guide"""
    return f"{datetime_to_format:%-I:%M%p}".lower() if datetime_to_format else ""


def amp_format_datetime(datetime_to_format: datetime) -> str:
    """Format date and time according to GDS style guide"""
    return (
        f"{amp_format_date(datetime_to_format)} {amp_format_time(datetime_to_format)}"
        if datetime_to_format
        else ""
    )


def undo_double_escapes(html: str) -> str:
    """Undo double escapes, where & has been replaced with &amp; in escaped html"""
    return (
        html.replace("&amp;lt;", "&lt;")
        .replace("&amp;gt;", "&gt;")
        .replace("&amp;quot;", "&quot;")
    )


def checks_if_2fa_is_enabled(user: User) -> bool:
    """Checks if 2FA is enabled for user"""
    return (
        EmailDevice.objects.filter(user=user).exists()
        and EmailDevice.objects.get(user=user).confirmed
    )


def check_dict_for_truthy_values(dictionary: Dict, keys_to_check: List[str]) -> bool:
    """Check list of keys in dictionary for at least one truthy value"""
    return len([True for field_name in keys_to_check if dictionary.get(field_name)]) > 0


def calculate_current_month_progress(
    label: str, number_done_this_month: int, number_done_last_month: int
) -> Dict[str, Union[str, int]]:
    """
    Given the current day of the month compare a number of things done
    to date in the current month to the total done in the previous month
    and express as a percentage above or below.
    """
    now: datetime = timezone.now()
    days_in_current_month: int = calendar.monthrange(now.year, now.month)[1]
    metric: Dict[str, Union[str, int]] = {
        "label": label,
        "number_done_this_month": number_done_this_month,
        "number_done_last_month": number_done_last_month,
    }
    if number_done_last_month == 0:
        return metric

    percentage_progress: int = int(
        (
            (number_done_this_month / (now.day / days_in_current_month))
            / number_done_last_month
        )
        * 100
    )
    expected_progress_difference: int = percentage_progress - 100
    expected_progress_difference_label: str = (
        "under" if expected_progress_difference < 0 else "over"
    )
    metric["expected_progress_difference"] = abs(expected_progress_difference)
    metric["expected_progress_difference_label"] = expected_progress_difference_label
    return metric


def build_yearly_metric_chart(
    label: str, all_table_rows: List[Dict[str, Union[datetime, int]]]
) -> Dict[
    str,
    Union[
        str,
        int,
        List[Dict[str, Union[datetime, int]]],
        List[Dict[str, Union[str, int]]],
    ],
]:
    """
    Given numbers of things done each month, derive the values needed to draw
    a line chart.
    """
    x_position: int = 0
    max_value: int = max([table_row["count"] for table_row in all_table_rows])  # type: ignore
    for table_row in all_table_rows:
        if max_value > 100:
            table_row["y"] = GRAPH_HEIGHT - table_row["count"]  # type: ignore
        else:
            table_row["y"] = GRAPH_HEIGHT - (table_row["count"] * MULTIPLIER_100_TO_250)  # type: ignore
        table_row["x"] = x_position
        x_position = x_position + X_AXIS_STEP
    last_x_position: int = all_table_rows[-1]["x"]  # type: ignore
    y_axis_labels: List[Dict[str, Union[str, int]]] = (
        Y_AXIS_LABELS_250 if max_value > 100 else Y_AXIS_LABELS_100
    )
    return {
        "label": label,
        "all_table_rows": all_table_rows,
        "previous_month_rows": all_table_rows[:-1],
        "current_month_rows": all_table_rows[-2:],
        "graph_height": GRAPH_HEIGHT,
        "chart_height": GRAPH_HEIGHT + CHART_HEIGHT_EXTRA,
        "chart_width": last_x_position + CHART_WIDTH_EXTRA,
        "last_x_position": last_x_position,
        "x_axis_tick_y2": GRAPH_HEIGHT + X_AXIS_TICK_HEIGHT,
        "x_axis_label_1_y": GRAPH_HEIGHT + X_AXIS_LABEL_1_Y_OFFSET,
        "x_axis_label_2_y": GRAPH_HEIGHT + X_AXIS_LABEL_2_Y_OFFSET,
        "y_axis_labels": y_axis_labels,
    }
