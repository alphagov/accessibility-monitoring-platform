"""
Test - common utility functions
"""
import pytest
from unittest.mock import patch

from typing import Any, Dict, List, Tuple, Union
import csv
from datetime import date, datetime, timedelta
import io
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import HttpResponse
from django.http.request import QueryDict
from django.utils import timezone

from django_otp.plugins.otp_email.models import EmailDevice


from ..models import (
    Event,
    Platform,
    EVENT_TYPE_MODEL_CREATE,
    EVENT_TYPE_MODEL_UPDATE,
    ChangeToPlatform,
)
from ..utils import (
    build_filters,
    download_as_csv,
    extract_domain_from_url,
    amp_format_date,
    amp_format_datetime,
    amp_format_time,
    get_id_from_button_name,
    convert_date_to_datetime,
    validate_url,
    get_platform_settings,
    get_recent_changes_to_platform,
    record_model_create_event,
    record_model_update_event,
    list_to_dictionary_of_lists,
    undo_double_escapes,
    checks_if_2fa_is_enabled,
    check_dict_for_truthy_values,
    calculate_current_month_progress,
    build_yearly_metric_chart,
)


class MockModel:
    def __init__(self, integer_field, char_field):
        self.integer_field = integer_field
        self.char_field = char_field
        self.field_not_in_csv = "field_not_in_csv"


MOCK_MODEL_FIELDS: List[str] = ["integer_field", "char_field"]
MOCK_MODEL_DATA: List[List[str]] = [["1", "char1"], ["2", "char2"]]
MOCK_QUERYSET: List[MockModel] = [
    MockModel(integer_field=1, char_field="char1"),
    MockModel(integer_field=2, char_field="char2"),
]
CSV_FILENAME: str = "filename.csv"
METRIC_LABEL: str = "Metric label"


def get_csv_response() -> HttpResponse:
    """Call download_as_csv and return response"""
    return download_as_csv(
        queryset=MOCK_QUERYSET,  # type: ignore
        field_names=MOCK_MODEL_FIELDS,
        filename=CSV_FILENAME,
    )


def get_csv_data_header_and_body() -> Tuple[List[str], List[List[str]]]:
    """Get the csv data and return the headers and body separately"""
    response: HttpResponse = get_csv_response()
    content: str = response.content.decode("utf-8")
    cvs_reader: Any = csv.reader(io.StringIO(content))
    csv_body: List[List[str]] = list(cvs_reader)
    csv_header: List[str] = csv_body.pop(0)
    return csv_header, csv_body


def test_response_code_is_200():
    """Tests whether the download function response has status code 200"""
    response: HttpResponse = get_csv_response()
    assert response.status_code == 200


def test_response_headers_contains_filename():
    """Tests that the response headers contains the requested file name"""
    response: HttpResponse = get_csv_response()
    assert (
        response.headers["Content-Disposition"]  # type: ignore
        == f"attachment; filename={CSV_FILENAME}"
    )


def test_csv_header_is_as_expected():
    """Tests that the csv header matches the list of fields"""
    csv_header, _ = get_csv_data_header_and_body()
    assert csv_header == MOCK_MODEL_FIELDS


def test_csv_body_is_as_expected():
    """Tests that the csv data matches that returned by the queryset"""
    _, csv_body = get_csv_data_header_and_body()
    assert csv_body == MOCK_MODEL_DATA


def test_extract_domain_from_url_https():
    """Tests that the domain is extracted from a url with https protocol"""
    assert (
        extract_domain_from_url(url="https://example.com/index.html") == "example.com"
    )


def test_extract_domain_from_url_http():
    """Tests that the domain is extracted from a url with http protocol"""
    assert extract_domain_from_url(url="http://example.com") == "example.com"


def test_extract_domain_from_url_no_protocol():
    """Tests that the domain is not extracted from a url with no protocol"""
    assert extract_domain_from_url(url="example.com") == ""


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
    field_and_filter_names: List[Tuple[str, str]] = [
        ("case_number", "id"),
        ("domain", "domain__icontains"),
    ]
    fields_data: Dict[str, Any] = {
        "case_number": "42",
        "domain": "domain name",
        "unused_field": "unused value",
    }
    expected_filters: Dict[str, str] = {
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

    assert platform.id == 1  # type: ignore


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

    recent_changes_to_platform: QuerySet[
        ChangeToPlatform
    ] = get_recent_changes_to_platform()

    assert recent_changes_to_platform.count() == 1
    assert recent_change_to_platform in recent_changes_to_platform


@pytest.mark.django_db
def test_record_model_create_event():
    """Test creation of model create event"""
    user: User = User.objects.create()
    record_model_create_event(user=user, model_object=user)

    content_type: ContentType = ContentType.objects.get_for_model(User)
    event: Event = Event.objects.get(content_type=content_type, object_id=user.id)  # type: ignore

    assert event.type == EVENT_TYPE_MODEL_CREATE


@pytest.mark.django_db
def test_record_model_update_event():
    """Test creation of model update event"""
    user: User = User.objects.create()
    record_model_update_event(user=user, model_object=user)

    content_type: ContentType = ContentType.objects.get_for_model(User)
    event: Event = Event.objects.get(content_type=content_type, object_id=user.id)  # type: ignore

    assert event.type == EVENT_TYPE_MODEL_UPDATE


def test_list_to_dictionary_of_lists():
    """Test list of items grouped by attribute and converted to dictionary of lists"""
    mock_1: MockModel = MockModel(char_field="key1", integer_field=1)
    mock_2: MockModel = MockModel(char_field="key1", integer_field=2)
    mock_3: MockModel = MockModel(char_field="key2", integer_field=3)
    mock_4: MockModel = MockModel(char_field="key3", integer_field=4)
    mocks: List[MockModel] = [mock_1, mock_2, mock_3, mock_4]

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
def test_check_dict_for_truthy_values(dictionary, keys_to_check, expected_result):
    """
    Test dictionary contains at least one truthy values for list of keys to check.
    """
    assert check_dict_for_truthy_values(dictionary, keys_to_check) == expected_result


@pytest.mark.parametrize(
    "day_of_month, number_done_this_month, number_done_last_month, expected_metric",
    [
        (
            31,
            15,
            30,
            {
                "expected_progress_difference": 50,
                "expected_progress_difference_label": "under",
            },
        ),
        (
            31,
            45,
            30,
            {
                "expected_progress_difference": 50,
                "expected_progress_difference_label": "over",
            },
        ),
        (
            1,
            5,
            30,
            {
                "expected_progress_difference": 416,
                "expected_progress_difference_label": "over",
            },
        ),
        (
            31,
            45,
            0,
            {},
        ),
    ],
)
@patch("accessibility_monitoring_platform.apps.common.utils.timezone")
def test_calculate_current_month_progress(
    mock_timezone,
    day_of_month,
    number_done_this_month,
    number_done_last_month,
    expected_metric,
):
    """
    Test calculation of progress through current month
    """
    mock_timezone.now.return_value = datetime(2022, 12, day_of_month)
    expected_metric["label"] = METRIC_LABEL
    expected_metric["number_done_this_month"] = number_done_this_month
    expected_metric["number_done_last_month"] = number_done_last_month

    assert expected_metric == calculate_current_month_progress(
        label=METRIC_LABEL,
        number_done_this_month=number_done_this_month,
        number_done_last_month=number_done_last_month,
    )


def test_build_yearly_metric_chart():
    """
    Test building of yearly metric data for line chart
    """
    label: str = "Label"
    all_table_rows: List[Dict[str, Union[datetime, int]]] = [
        {"month_date": datetime(2021, 11, 1), "count": 42},
        {"month_date": datetime(2021, 12, 1), "count": 54},
        {"month_date": datetime(2022, 1, 1), "count": 45},
        {"month_date": datetime(2022, 2, 1), "count": 20},
        {"month_date": datetime(2022, 3, 1), "count": 64},
        {"month_date": datetime(2022, 4, 1), "count": 22},
        {"month_date": datetime(2022, 5, 1), "count": 44},
        {"month_date": datetime(2022, 6, 1), "count": 42},
        {"month_date": datetime(2022, 7, 1), "count": 45},
        {"month_date": datetime(2022, 8, 1), "count": 49},
        {"month_date": datetime(2022, 9, 1), "count": 52},
        {"month_date": datetime(2022, 10, 1), "count": 54},
        {"month_date": datetime(2022, 11, 1), "count": 8},
    ]
    assert build_yearly_metric_chart(label=label, all_table_rows=all_table_rows) == {
        "label": label,
        "all_table_rows": all_table_rows,
        "previous_month_rows": all_table_rows[:-1],
        "current_month_rows": all_table_rows[-2:],
        "chart_height": 114,
        "chart_width": 750,
        "last_x_position": 600,
        "max_value": 64,
        "x_axis_tick_y2": 74,
        "x_axis_label_1_y": 89,
        "x_axis_label_2_y": 109,
    }
