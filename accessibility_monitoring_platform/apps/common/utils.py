""" Common utility functions """
from datetime import date, datetime, timedelta

import re
import json
from typing import (
    Any,
    Dict,
    List,
    Match,
    Optional,
    Tuple,
    Union,
)
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.http.request import QueryDict
from django.utils import timezone

from django_otp.plugins.otp_email.models import EmailDevice

from .models import Event, Platform, EVENT_TYPE_MODEL_CREATE, ChangeToPlatform


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
