""" Common utility functions """

import json
import re
import urllib
from datetime import date, datetime, timedelta
from datetime import timezone as datetime_timezone
from typing import Any, Dict, Iterable, List, Match, Optional, Tuple, Union
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http.request import QueryDict
from django.utils import timezone
from django_otp.plugins.otp_email.models import EmailDevice

from .models import ChangeToPlatform, Event, Platform


def extract_domain_from_url(url: str) -> str:
    """Extract and return domain string from url string"""
    domain_match: Union[Match[str], None] = re.search(
        "https?://([A-Za-z_0-9.-]+).*", url
    )
    return domain_match.group(1) if domain_match else ""


def sanitise_domain(domain: str) -> str:
    """Remove common parts from domain to return unique bit"""
    if domain.startswith("www."):
        domain = domain[4:]

    for dot_gov in [".gov.", ".nhs."]:
        dot_gov_position: int = domain.find(dot_gov)
        if dot_gov_position >= 0:
            domain = domain[:dot_gov_position]
    for suffix in [
        ".com",
        ".wales",
        ".cymru",
        ".scot",
        ".eu",
        ".co.uk",
        ".org.uk",
        ".ac.uk",
    ]:
        if domain.endswith(suffix):
            domain = domain[: -len(suffix)]
    return domain


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


def get_days_ago_timestamp(days: int = 30) -> datetime:
    """
    Subtract number of days from today's date and return a timezone-aware
    timestamp of midnight on that date.
    """
    today: date = date.today()
    days_ago_date: date = today - timedelta(days=days)
    return datetime.combine(
        days_ago_date, datetime.min.time(), tzinfo=datetime_timezone.utc
    )


def record_model_update_event(user: User, model_object: models.Model) -> None:
    """Record model update event"""
    value: Dict[str, str] = {}
    old_model = model_object.__class__.objects.get(pk=model_object.id)
    value["old"] = serializers.serialize("json", [old_model])
    value["new"] = serializers.serialize("json", [model_object])
    if value["old"] != value["new"]:
        Event.objects.create(
            created_by=user, parent=model_object, value=json.dumps(value)
        )


def record_model_create_event(user: User, model_object: models.Model) -> None:
    """Record model create event"""
    value: Dict[str, str] = {"new": serializers.serialize("json", [model_object])}
    Event.objects.create(
        created_by=user,
        parent=model_object,
        type=Event.Type.CREATE,
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


def format_outstanding_issues(
    failed_checks_count: int = 0, fixed_checks_count: int = 0
) -> str:
    """Return string showing how many outstanding issues there are"""
    if failed_checks_count == 0:
        return "0 of 0 fixed"
    percentage: int = int(fixed_checks_count * 100 / failed_checks_count)
    return f"{fixed_checks_count} of {failed_checks_count} fixed ({percentage}%)"


def format_statement_check_overview(
    tests_passed: int = 0,
    tests_failed: int = 0,
    retests_passed: int = 0,
    retests_failed: int = 0,
) -> str:
    """Return string showing how many statement checks have failed"""
    if tests_passed == 0 and tests_failed == 0:
        return "No test results"

    if tests_passed > 0 and tests_failed == 0 and retests_failed == 0:
        return "Fully compliant"

    result: str = f"{tests_failed} checks failed on test"

    if retests_passed > 0 or retests_failed > 0:
        result += f" ({retests_failed} on 12-week retest)"

    return result


def get_dict_without_page_items(items: Iterable[Tuple[str, str]]) -> Dict[str, str]:
    """Remove tuples beginning with 'page' from iterable"""
    return {key: value for (key, value) in items if key != "page"}


def get_url_parameters_for_pagination(request: HttpRequest):
    """Get URL parameters from GET removing existing 'page' parameter"""
    return urllib.parse.urlencode(get_dict_without_page_items(request.GET.items()))


def get_first_of_this_month_last_year() -> datetime:
    """Calculate and return the first of this month last year"""
    now: datetime = timezone.now()
    return datetime(now.year - 1, now.month, 1, tzinfo=datetime_timezone.utc)


def get_one_year_ago():
    """Calculate and return timestamp of midnight one year ago"""
    today: date = date.today()
    if today.month == 2 and today.day == 29:
        today -= timedelta(days=1)
    one_year_ago: datetime = datetime(
        today.year - 1, today.month, today.day, 0, 0, tzinfo=datetime_timezone.utc
    )
    return one_year_ago
