"""
Test - common utility functions
"""
import pytest
import csv
from datetime import date, datetime
import io
import pytz
from typing import Any, Dict, List, Tuple

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.http.request import QueryDict

from ..utils import (
    build_filters,
    download_as_csv,
    extract_domain_from_url,
    get_id_from_button_name,
    convert_date_to_datetime,
    validate_url,
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


def get_csv_response() -> HttpResponse:
    """Call download_as_csv and return response"""
    return download_as_csv(
        queryset=MOCK_QUERYSET,
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
        response.headers["Content-Disposition"]
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
    button_id: int = "not_a_number"
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
    expected_datetime: datetime = datetime(year=2021, month=6, day=10, tzinfo=pytz.UTC)
    assert convert_date_to_datetime(input_date) == expected_datetime


def test_convert_date_plus_hour_minute_second_to_datetime():
    """Test date plus hour, minute and second arguments is converted to datetime correctly"""
    input_date: date = date(year=2021, month=6, day=10)
    expected_datetime: datetime = datetime(
        year=2021, month=6, day=10, hour=1, minute=2, second=3, tzinfo=pytz.UTC
    )
    assert (
        convert_date_to_datetime(input_date, hour=1, minute=2, second=3)
        == expected_datetime
    )


@pytest.mark.parametrize("url", ["https://gov.uk", "http://example.com"])
def test_validate_url_raises_no_error(url):
    """Test url_validation raises no error for a valid url"""
    validation_result = validate_url(url)

    assert validation_result is None


def test_validate_url_raises_validation_error():
    """Test url_validation raises validation error for invalid url"""
    with pytest.raises(ValidationError) as excinfo:
        validate_url("no protocol")

    assert "URL must start with http:// or https://" in str(excinfo.value)
