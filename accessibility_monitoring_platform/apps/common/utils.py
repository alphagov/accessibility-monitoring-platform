""" Common utility functions """

import copy
import json
import re
import urllib
from collections.abc import Iterable
from datetime import date, datetime, timedelta
from datetime import timezone as datetime_timezone
from typing import Any, Match
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http.request import QueryDict
from django.utils import timezone
from django_otp.plugins.otp_email.models import EmailDevice

from .models import ChangeToPlatform, Event, Platform

SESSION_EXPIRY_WARNING_WINDOW: timedelta = timedelta(hours=12)


class SessionExpiry:
    def __init__(self, request: HttpRequest):
        if hasattr(request, "session"):
            self.session_expiry_date: datetime = request.session.get_expiry_date()
            self.show_session_expiry_warning: bool = (
                timezone.now() + SESSION_EXPIRY_WARNING_WINDOW
                > self.session_expiry_date
            )
        else:
            self.session_expiry_date = None
            self.show_session_expiry_warning = False


def extract_domain_from_url(url: str) -> str:
    """Extract and return domain string from url string"""
    if url.startswith("https://"):
        url = url[8:]
    elif url.startswith("http://"):
        url = url[7:]
    domain_match: Match[str] | None = re.search("([A-Za-z_0-9.-]+).*", url)
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
        ".net",
    ]:
        if domain.endswith(suffix):
            domain = domain[: -len(suffix)]
    return domain


def get_id_from_button_name(
    button_name_prefix: str, querydict: QueryDict
) -> int | None:
    """
    Given a button name in the form: prefix_[id] extract and return the id value.
    """
    key_names: list[str] = [
        key for key in querydict.keys() if key.startswith(button_name_prefix)
    ]
    object_id: int | None = None
    if len(key_names) == 1:
        id_string: str = key_names[0].replace(button_name_prefix, "")
        object_id: int | None = int(id_string) if id_string.isdigit() else None
    return object_id


def mark_object_as_deleted(
    request: HttpRequest, delete_button_prefix: str, object_to_delete_model
) -> None:
    """
    Check for delete/remove button in request. Mark object as deleted.
    """
    object_id_to_delete: int | None = get_id_from_button_name(
        button_name_prefix=delete_button_prefix,
        querydict=request.POST,
    )
    if object_id_to_delete is not None:
        object_to_delete = object_to_delete_model.objects.get(id=object_id_to_delete)
        object_to_delete.is_deleted = True
        record_model_update_event(user=request.user, model_object=object_to_delete)
        object_to_delete.save()


def build_filters(
    cleaned_data: dict, field_and_filter_names: list[tuple[str, str]]
) -> dict[str, Any]:
    """
    Given the form cleaned_data, work through a list of field and filter names
    to build up a dictionary of filters to apply in a queryset.
    """
    filters: dict[str, Any] = {}
    for field_name, filter_name in field_and_filter_names:
        value: str | None = cleaned_data.get(field_name)
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
    try:
        return Platform.objects.get(pk=1)
    except Platform.DoesNotExist:
        platform: Platform = Platform.objects.create()
        return platform


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


def diff_model_fields(
    old_fields: dict[str, Any], new_fields: dict[str, Any]
) -> dict[str, Any]:
    """Return differences between old and new values of fields"""
    if not old_fields:
        return new_fields
    diff_fields = {}
    for key in new_fields:
        if key in old_fields:
            if old_fields[key] != new_fields[key]:
                diff_fields[key] = f"{old_fields[key]} -> {new_fields[key]}"
        else:
            diff_fields[key] = f"-> {new_fields[key]}"
    for key in old_fields:
        if key not in new_fields:
            diff_fields[key] = f"{old_fields[key]} ->"
    return diff_fields


def record_model_update_event(user: User, model_object: models.Model) -> None:
    """Record model update event"""
    old_model = model_object.__class__.objects.get(pk=model_object.id)
    old_model_fields = copy.copy(vars(old_model))
    del old_model_fields["_state"]
    new_model_fields = copy.copy(vars(model_object))
    del new_model_fields["_state"]
    diff_fields: dict[str, Any] = diff_model_fields(
        old_fields=old_model_fields, new_fields=new_model_fields
    )
    if diff_fields:
        Event.objects.create(
            created_by=user,
            parent=model_object,
            value=json.dumps(diff_fields, default=str),
        )


def record_model_create_event(user: User, model_object: models.Model) -> None:
    """Record model create event"""
    new_model_fields = copy.copy(vars(model_object))
    del new_model_fields["_state"]
    Event.objects.create(
        created_by=user,
        parent=model_object,
        type=Event.Type.CREATE,
        value=json.dumps(new_model_fields, default=str),
    )


def list_to_dictionary_of_lists(
    items: list[Any], group_by_attr: str
) -> dict[Any, list[Any]]:
    """
    Group a list of items by an attribute of those items and return a dictionary
    with that attribute as the key and the value being a list of items matching the attribute.

    """
    dict_of_lists_of_items: dict[Any, list[Any]] = {}
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


def check_dict_for_truthy_values(dictionary: dict, keys_to_check: list[str]) -> bool:
    """Check list of keys in dictionary for at least one truthy value"""
    return len([True for field_name in keys_to_check if dictionary.get(field_name)]) > 0


def calculate_percentage(total: int, partial: int) -> int:
    """Return partial as a percentage of total or zero"""
    if total == 0:
        return 0
    return int(partial * 100 / total)


def format_outstanding_issues(
    failed_checks_count: int = 0, fixed_checks_count: int = 0
) -> str:
    """Return string showing how many outstanding issues there are"""
    if failed_checks_count == 0:
        return "0 of 0 fixed"
    percentage: int = calculate_percentage(
        total=failed_checks_count, partial=fixed_checks_count
    )
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


def get_dict_without_page_items(items: Iterable[tuple[str, str]]) -> dict[str, str]:
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
