"""
Test - common utility functions
"""

import json
from datetime import date, datetime, timedelta
from datetime import timezone as datetime_timezone
from typing import Any
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http.request import QueryDict
from django.utils import timezone
from django_otp.plugins.otp_email.models import EmailDevice

from ...cases.models import Case, Contact
from ..models import ChangeToPlatform, Event, Platform
from ..utils import (
    SessionExpiry,
    amp_format_date,
    amp_format_datetime,
    amp_format_time,
    build_filters,
    calculate_percentage,
    check_dict_for_truthy_values,
    checks_if_2fa_is_enabled,
    convert_date_to_datetime,
    diff_model_fields,
    extract_domain_from_url,
    format_outstanding_issues,
    format_statement_check_overview,
    get_days_ago_timestamp,
    get_dict_without_page_items,
    get_first_of_this_month_last_year,
    get_id_from_button_name,
    get_one_year_ago,
    get_platform_settings,
    get_recent_changes_to_platform,
    get_url_parameters_for_pagination,
    list_to_dictionary_of_lists,
    mark_object_as_deleted,
    record_model_create_event,
    record_model_update_event,
    sanitise_domain,
    undo_double_escapes,
    validate_url,
)

CHANGED_FIELD_OLD_FIELDS: str = {"field1": "value1", "field2": "value2"}
CHANGED_FIELD_NEW_FIELDS: str = {"field1": "value1a", "field2": "value2"}
CHANGED_FIELD_DIFF: str = {"field1": "value1 -> value1a"}

CREATE_ROW_OLD_FIELDS: str = ""
CREATE_ROW_NEW_FIELDS: str = {"field1": "value1", "field2": "value2"}

ADD_FIELD_OLD_FIELDS: str = {"field1": "value1"}
ADD_FIELD_NEW_FIELDS: str = {"field1": "value1", "field2": "value2"}
ADD_FIELD_DIFF: str = {"field2": "-> value2"}

REMOVE_FIELD_OLD_FIELDS: str = {"field1": "value1", "field2": "value2"}
REMOVE_FIELD_NEW_FIELDS: str = {"field1": "value1"}
REMOVE_FIELD_DIFF: str = {"field2": "value2 ->"}


class MockModel:
    def __init__(self, integer_field, char_field):
        self.integer_field = integer_field
        self.char_field = char_field
        self.field_not_in_csv = "field_not_in_csv"


class MockSession:
    def __init__(self, expiry_date: datetime):
        self.expiry_date = expiry_date

    def get_expiry_date(self):
        return self.expiry_date


class MockRequest:
    def __init__(
        self,
        button: str = "Save",
        user: User | None = None,
        session: MockSession | None = None,
    ):
        self.POST = {button: "Remove"}
        self.user = user
        self.session = session


def test_extract_domain_from_url_https():
    """Tests that the domain is extracted from a url with https protocol"""
    assert (
        extract_domain_from_url(url="https://example.com/index.html") == "example.com"
    )


def test_extract_domain_from_url_http():
    """Tests that the domain is extracted from a url with http protocol"""
    assert extract_domain_from_url(url="http://example.com") == "example.com"


def test_extract_domain_from_url_no_protocol():
    """Tests that the domain is extracted from a url with no protocol"""
    assert extract_domain_from_url(url="example.com") == "example.com"


@pytest.mark.parametrize(
    "domain, expected_result",
    [
        ("www.abc", "abc"),
        ("abc", "abc"),
        ("abc.gov.uk", "abc"),
        ("abc.nhs.uk", "abc"),
        ("abc.gov.uk", "abc"),
        ("abc.gov.uk", "abc"),
        ("abc.com", "abc"),
        ("abc.wales", "abc"),
        ("abc.cymru", "abc"),
        ("abc.scot", "abc"),
        ("abc.eu", "abc"),
        ("abc.co.uk", "abc"),
        ("abc.org.uk", "abc"),
        ("abc.ac.uk", "abc"),
        ("abc.net", "abc"),
    ],
)
def test_sanitise_domain(domain: str, expected_result: str):
    """Tests that the domain is not extracted from a url with no protocol"""
    assert sanitise_domain(domain) == expected_result


def test_get_id_from_button_name():
    """Tests that the id is extracted from a button name with known prefix"""
    button_name_prefix: str = "prefix_"
    button_id: int = 1
    button_name: str = f"{button_name_prefix}{button_id}"
    querydict: QueryDict = QueryDict(f"meh=val&{button_name}=1&a=2&c=3")
    assert (
        get_id_from_button_name(
            button_name_prefix=button_name_prefix, querydict=querydict
        )
        == button_id
    )


@pytest.mark.django_db
def test_mark_object_as_deleted():
    """Tests that object is marked as deleted"""
    delete_button_prefix = "delete_button_prefix_"
    case: Case = Case.objects.create()
    contact: Contact = Contact.objects.create(case=case)
    user: User = User.objects.create()
    mock_request: MockRequest = MockRequest(
        button=f"{delete_button_prefix}{contact.id}",
        user=user,
    )

    assert contact.is_deleted is False

    mark_object_as_deleted(
        request=mock_request,
        delete_button_prefix=delete_button_prefix,
        object_to_delete_model=Contact,
    )

    contact_from_db: Contact = Contact.objects.get(id=contact.id)

    assert contact_from_db.is_deleted is True


def test_get_non_numeric_suffix_from_button_name():
    """Tests that the a non-integer button name suffix returns None"""
    button_name_prefix: str = "prefix_"
    button_id: str = "not_a_number"
    button_name: str = f"{button_name_prefix}{button_id}"
    querydict: QueryDict = QueryDict(f"meh=val&{button_name}=1&a=2&c=3")
    assert (
        get_id_from_button_name(
            button_name_prefix=button_name_prefix, querydict=querydict
        )
        is None
    )


def test_get_no_id_from_button_name_with_wrong_prefix():
    """Tests that no id is extracted from a button name with wrong prefix"""
    button_name_prefix: str = "prefix_"
    button_name: str = f"wrong_prefix_{button_name_prefix}1"
    querydict: QueryDict = QueryDict(f"{button_name}=1&a=2&c=3")
    assert (
        get_id_from_button_name(
            button_name_prefix=button_name_prefix, querydict=querydict
        )
        is None
    )


def test_build_filters_from_field_values():
    """Tests that filter dictionary is build from field values"""
    field_and_filter_names: list[tuple[str, str]] = [
        ("case_number", "id"),
        ("domain", "domain__icontains"),
    ]
    fields_data: dict[str, Any] = {
        "case_number": "42",
        "domain": "domain name",
        "unused_field": "unused value",
    }
    expected_filters: dict[str, str] = {
        "id": "42",
        "domain__icontains": "domain name",
    }
    assert (
        build_filters(
            cleaned_data=fields_data, field_and_filter_names=field_and_filter_names
        )
        == expected_filters
    )


def test_convert_date_to_datetime():
    """Test date is converted to datetime correctly"""
    input_date: date = date(year=2021, month=6, day=10)
    expected_datetime: datetime = datetime(
        year=2021, month=6, day=10, tzinfo=ZoneInfo("UTC")
    )
    assert convert_date_to_datetime(input_date) == expected_datetime


def test_convert_date_plus_hour_minute_second_to_datetime():
    """Test date plus hour, minute and second arguments is converted to datetime correctly"""
    input_date: date = date(year=2021, month=6, day=10)
    expected_datetime: datetime = datetime(
        year=2021, month=6, day=10, hour=1, minute=2, second=3, tzinfo=ZoneInfo("UTC")
    )
    assert (
        convert_date_to_datetime(input_date, hour=1, minute=2, second=3)
        == expected_datetime
    )


@pytest.mark.parametrize("url", ["https://gov.uk", "http://example.com"])
def test_validate_url_raises_no_error(url):
    """Test url_validation raises no error for a valid url"""
    assert validate_url(url) is None


def test_validate_url_raises_validation_error():
    """Test url_validation raises validation error for invalid url"""
    with pytest.raises(ValidationError) as excinfo:
        validate_url("no protocol")

    assert "URL must start with http:// or https://" in str(excinfo.value)


@pytest.mark.django_db
def test_get_platform_settings():
    """Test get_platform_settings returns the platform settings row"""
    platform: Platform = get_platform_settings()

    assert platform.id == 1


@pytest.mark.django_db
def test_get_recent_changes_to_platform():
    """
    Test get_recent_changes_to_platform returne platform changes made in last 24 hours
    """
    older_change_to_platform: ChangeToPlatform = ChangeToPlatform.objects.create(
        name="Older"
    )
    older_change_to_platform.created = timezone.now() - timedelta(hours=25)
    older_change_to_platform.save()
    recent_change_to_platform: ChangeToPlatform = ChangeToPlatform.objects.create(
        name="Recent"
    )

    recent_changes_to_platform: QuerySet[ChangeToPlatform] = (
        get_recent_changes_to_platform()
    )

    assert recent_changes_to_platform.count() == 1
    assert recent_change_to_platform in recent_changes_to_platform


@pytest.mark.django_db
def test_record_model_create_event():
    """Test creation of model create event"""
    user: User = User.objects.create()
    record_model_create_event(user=user, model_object=user)

    content_type: ContentType = ContentType.objects.get_for_model(User)
    event: Event = Event.objects.get(content_type=content_type, object_id=user.id)

    assert event.type == Event.Type.CREATE

    value_dict: dict[str, Any] = json.loads(event.value)

    assert "last_login" in value_dict
    assert value_dict["last_login"] is None
    assert "is_active" in value_dict
    assert value_dict["is_active"] is True
    assert "is_staff" in value_dict
    assert value_dict["is_staff"] is False


@pytest.mark.django_db
def test_record_model_update_event():
    """Test creation of model update event"""
    user: User = User.objects.create()
    user.first_name = "Changed"
    record_model_update_event(user=user, model_object=user)

    content_type: ContentType = ContentType.objects.get_for_model(User)
    event: Event = Event.objects.get(content_type=content_type, object_id=user.id)

    assert event.type == Event.Type.UPDATE
    assert event.value == '{"first_name": " -> Changed"}'


def test_list_to_dictionary_of_lists():
    """Test list of items grouped by attribute and converted to dictionary of lists"""
    mock_1: MockModel = MockModel(char_field="key1", integer_field=1)
    mock_2: MockModel = MockModel(char_field="key1", integer_field=2)
    mock_3: MockModel = MockModel(char_field="key2", integer_field=3)
    mock_4: MockModel = MockModel(char_field="key3", integer_field=4)
    mocks: list[MockModel] = [mock_1, mock_2, mock_3, mock_4]

    assert list_to_dictionary_of_lists(items=mocks, group_by_attr="char_field") == {
        "key1": [mock_1, mock_2],
        "key2": [mock_3],
        "key3": [mock_4],
    }


@pytest.mark.parametrize(
    "date_to_format,expected_result",
    [
        (date(2021, 4, 1), "1 April 2021"),
        (None, ""),
    ],
)
def test_amp_format_date(date_to_format, expected_result):
    """Test date formatted according to GDS style guide."""
    assert amp_format_date(date_to_format) == expected_result


@pytest.mark.parametrize(
    "datetime_to_format,expected_result",
    [
        (datetime(2021, 4, 1, 9, 1), "9:01am"),
        (None, ""),
    ],
)
def test_amp_format_time(datetime_to_format, expected_result):
    """Test time formatted according to GDS style guide."""
    assert amp_format_time(datetime_to_format) == expected_result


@pytest.mark.parametrize(
    "datetime_to_format,expected_result",
    [
        (datetime(2021, 4, 1, 9, 1), "1 April 2021 9:01am"),
        (None, ""),
    ],
)
def test_amp_format_datetime(datetime_to_format, expected_result):
    """Test date and time formatted according to GDS style guide."""
    assert amp_format_datetime(datetime_to_format) == expected_result


def test_undo_double_escapes():
    """
    Test Undo double escapes, where & has been replaced with &amp; in escaped html
    """
    assert undo_double_escapes("&amp;lt;tag&amp;gt;&amp;quot;") == "&lt;tag&gt;&quot;"


@pytest.mark.django_db
def test_checks_if_2fa_is_enabled():
    """Test to check whether checks_if_2fa_is_enabled works as expected"""
    user: User = User.objects.create(
        email="uesr@email.com",
        password="123456",
    )

    assert checks_if_2fa_is_enabled(user=user) is False

    email_device: EmailDevice = EmailDevice.objects.create(
        user=user,
        name="default",
        confirmed=False,
    )

    assert checks_if_2fa_is_enabled(user=user) is False

    email_device.confirmed = True
    email_device.save()

    assert checks_if_2fa_is_enabled(user=user) is True


@pytest.mark.parametrize(
    "dictionary,keys_to_check,expected_result",
    [
        ({}, ["missing_key"], False),
        ({"truthy_key": True}, ["truthy_key"], True),
        ({"truthy_key": True, "falsey_key": False}, ["falsey_key"], False),
        (
            {"truthy_key_1": True, "truthy_key_2": True},
            ["truthy_key_1", "truthy_key_2"],
            True,
        ),
    ],
)
def test_check_dict_for_truthy_values(
    dictionary: dict[str, bool], keys_to_check: list[str], expected_result: bool
):
    """
    Test dictionary contains at least one truthy values for list of keys to check.
    """
    assert check_dict_for_truthy_values(dictionary, keys_to_check) == expected_result


@pytest.mark.parametrize(
    "failed_checks_count,fixed_checks_count,expected_result",
    [
        (0, 0, "0 of 0 fixed"),
        (10, 5, "5 of 10 fixed (50%)"),
        (9, 6, "6 of 9 fixed (66%)"),
    ],
)
def test_format_outstanding_issues(
    failed_checks_count: int, fixed_checks_count: int, expected_result: str
):
    assert (
        format_outstanding_issues(
            failed_checks_count=failed_checks_count,
            fixed_checks_count=fixed_checks_count,
        )
        == expected_result
    )


@pytest.mark.parametrize(
    "total,partial,expected_result",
    [
        (0, 0, 0),
        (0, 10, 0),
        (10, 0, 0),
        (10, 5, 50),
        (9, 6, 66),
    ],
)
def test_calculate_percentage(total: int, partial: int, expected_result: str):
    assert (
        calculate_percentage(
            total=total,
            partial=partial,
        )
        == expected_result
    )


@pytest.mark.parametrize(
    "tests_passed,tests_failed,retests_passed,retests_failed,expected_result",
    [
        (0, 0, 0, 0, "No test results"),
        (40, 0, 0, 0, "Fully compliant"),
        (40, 0, 40, 0, "Fully compliant"),
        (30, 10, 0, 0, "10 checks failed on test"),
        (35, 5, 30, 10, "5 checks failed on test (10 on 12-week retest)"),
    ],
)
def test_format_statement_check_overview(
    tests_passed,
    tests_failed,
    retests_passed,
    retests_failed,
    expected_result,
):
    assert (
        format_statement_check_overview(
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            retests_passed=retests_passed,
            retests_failed=retests_failed,
        )
        == expected_result
    )


@pytest.mark.parametrize(
    "items, expected_result",
    [
        ([], {}),
        ([("page", "1")], {}),
        ([("a", "b")], {"a": "b"}),
        ([("page", "1"), ("a", "b")], {"a": "b"}),
    ],
)
def test_get_dict_without_page_items(items, expected_result):
    """Test tuples beginning with 'page' are removed"""
    assert get_dict_without_page_items(items) == expected_result


@pytest.mark.parametrize(
    "get_parameters, expected_result",
    [
        ("", ""),
        ("?a=b", "a=b"),
        ("?page=1&a=b", "a=b"),
        ("?page=2&statement_check_search=website", "statement_check_search=website"),
    ],
)
def test_get_url_parameters_for_pagination(get_parameters, expected_result, rf):
    """Test get_url_parameters_for_pagination"""
    request: HttpRequest = rf.get(f"/{get_parameters}")
    assert get_url_parameters_for_pagination(request=request) == expected_result


def test_get_days_ago_timestamp():
    """Test timestamp for a number of days ago is calculated"""
    with patch("accessibility_monitoring_platform.apps.common.utils.date") as mock_date:
        mock_date.today.return_value = date(2023, 2, 1)
        assert get_days_ago_timestamp() == datetime(
            2023, 1, 2, 0, 0, tzinfo=datetime_timezone.utc
        )  # 30 days before
        assert get_days_ago_timestamp(days=31) == datetime(
            2023, 1, 1, 0, 0, tzinfo=datetime_timezone.utc
        )  # 31 days before


@pytest.mark.parametrize(
    "now, expected_result",
    [
        (
            datetime(2023, 8, 25, 0, 0, tzinfo=datetime_timezone.utc),
            datetime(2022, 8, 1, 0, 0, tzinfo=datetime_timezone.utc),
        ),
        (
            datetime(2022, 1, 2, 0, 0, tzinfo=datetime_timezone.utc),
            datetime(2021, 1, 1, 0, 0, tzinfo=datetime_timezone.utc),
        ),
    ],
)
def test_get_first_of_this_month_last_year(now, expected_result):
    """Test first of this month last year is calculated"""
    with patch(
        "accessibility_monitoring_platform.apps.common.utils.timezone"
    ) as mock_timezone:
        mock_timezone.now.return_value = now
        assert get_first_of_this_month_last_year() == expected_result


@pytest.mark.parametrize(
    "today, expected_result",
    [
        (
            date(2023, 8, 25),
            datetime(2022, 8, 25, 0, 0, tzinfo=datetime_timezone.utc),
        ),
        (
            date(2022, 1, 2),
            datetime(2021, 1, 2, 0, 0, tzinfo=datetime_timezone.utc),
        ),
    ],
)
def test_get_one_year_ago(today, expected_result):
    """Test midnight one year ago is calculated"""
    with patch("accessibility_monitoring_platform.apps.common.utils.date") as mock_date:
        mock_date.today.return_value = today
        assert get_one_year_ago() == expected_result


def test_session_expiry():
    """Test SessionExpiry contains time and boolean true if time is soon"""
    session_expiry_date: datetime = timezone.now() + timedelta(hours=1)
    mock_request: MockRequest = MockRequest(
        session=MockSession(expiry_date=session_expiry_date)
    )
    session_expiry: SessionExpiry = SessionExpiry(request=mock_request)

    assert session_expiry.session_expiry_date == session_expiry_date
    assert session_expiry.show_session_expiry_warning is True

    session_expiry_date: datetime = timezone.now() + timedelta(days=1)
    mock_request: MockRequest = MockRequest(
        session=MockSession(expiry_date=session_expiry_date)
    )
    session_expiry: SessionExpiry = SessionExpiry(request=mock_request)

    assert session_expiry.show_session_expiry_warning is False


@pytest.mark.parametrize(
    "old_fields, new_fields, expected_diff",
    [
        (
            CHANGED_FIELD_OLD_FIELDS,
            CHANGED_FIELD_NEW_FIELDS,
            CHANGED_FIELD_DIFF,
        ),
        (
            CREATE_ROW_OLD_FIELDS,
            CREATE_ROW_NEW_FIELDS,
            CREATE_ROW_NEW_FIELDS,
        ),
        (ADD_FIELD_OLD_FIELDS, ADD_FIELD_NEW_FIELDS, ADD_FIELD_DIFF),
        (
            REMOVE_FIELD_OLD_FIELDS,
            REMOVE_FIELD_NEW_FIELDS,
            REMOVE_FIELD_DIFF,
        ),
    ],
)
def test_diff_model_fields(old_fields, new_fields, expected_diff):
    """Test event diff contains expected value"""
    assert (
        diff_model_fields(old_fields=old_fields, new_fields=new_fields) == expected_diff
    )
