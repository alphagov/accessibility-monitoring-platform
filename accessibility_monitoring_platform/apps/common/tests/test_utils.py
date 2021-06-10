"""
Test - common utility functions
"""
import csv
import io
from typing import Any, List

from django.http import HttpResponse
from django.http.request import QueryDict
from django.test import TestCase

from ..utils import (
    build_filters,
    download_as_csv,
    extract_domain_from_url,
    get_id_from_button_name,
)


class MockModel():
    def __init__(self, integer_field, char_field):
        self.integer_field = integer_field
        self.char_field = char_field
        self.field_not_in_csv = "field_not_in_csv"


MOCK_MODEL_FIELDS = ["integer_field", "char_field"]
MOCK_MODEL_DATA = [["1", "char1"], ["2", "char2"]]
MOCK_QUERYSET = [
    MockModel(integer_field=1, char_field="char1"),
    MockModel(integer_field=2, char_field="char2"),
]
CSV_FILENAME = "filename.csv"


class DownloadAsCsvTests(TestCase):
    """
    Tests for download_as_csv

    Methods
    -------
    setUp()
        Sets up the test environment with a call to download_as_csv

    test_response_code_is_200()
        Tests whether the download function response has status code 200

    test_csv_header_is_as_expected()
        Tests that the csv header matches the list of fields

    test_csv_body_is_as_expected()
        Tests that the csv data matches that returned by the queryset
    """

    def setUp(self):
        self.response: HttpResponse = download_as_csv(
            queryset=MOCK_QUERYSET,
            field_names=MOCK_MODEL_FIELDS,
            filename=CSV_FILENAME,
        )
        content: str = self.response.content.decode("utf-8")
        cvs_reader: Any = csv.reader(io.StringIO(content))
        self.response_body: List[str] = list(cvs_reader)
        self.response_header: str = self.response_body.pop(0)

    def test_response_code_is_200(self):
        """ Tests whether the download function response has status code 200 """
        self.assertEqual(self.response.status_code, 200)

    def test_response_headers_contains_filename(self):
        """ Tests that the response headers contains the requested file name """
        self.assertEqual(
            self.response.headers["Content-Disposition"],
            f"attachment; filename={CSV_FILENAME}",
        )

    def test_csv_header_is_as_expected(self):
        """ Tests that the csv header matches the list of fields """
        self.assertEqual(self.response_header, MOCK_MODEL_FIELDS)

    def test_csv_body_is_as_expected(self):
        """ Tests that the csv data matches that returned by the queryset """
        self.assertEqual(self.response_body, MOCK_MODEL_DATA)


class ExtractDomainFromUrlTests(TestCase):
    """
    Tests for extract_domain_from_url

    Methods
    -------
    test_extract_domain_from_url_https()
        Tests that the domain is extracted from a url with https protocol

    test_extract_domain_from_url_http()
        Tests that the domain is extracted from a url with http protocol

    test_extract_domain_from_url_no_protocol()
        Tests that the domain is not extracted from a url with no protocol
    """

    def test_extract_domain_from_url_https(self):
        """ Tests that the domain is extracted from a url with https protocol """
        self.assertEqual(
            extract_domain_from_url(url="https://example.com/index.html"), "example.com"
        )

    def test_extract_domain_from_url_http(self):
        """ Tests that the domain is extracted from a url with http protocol """
        self.assertEqual(
            extract_domain_from_url(url="http://example.com"), "example.com"
        )

    def test_extract_domain_from_url_no_protocol(self):
        """ Tests that the domain is not extracted from a url with no protocol """
        self.assertEqual(extract_domain_from_url(url="example.com"), "")


class GetIdFromButtonName(TestCase):
    """
    Tests for get_id_from_button_name

    Methods
    -------
    test_get_id_from_button_name()
        Tests that the id is extracted from a button name with known prefix

    test_get_no_id_from_button_name_with_wrong_prefix()
        Tests that no id is extracted from a button name with wrong prefix
    """

    button_name_prefix = "prefix_"
    button_id = 0

    def test_get_id_from_button_name(self):
        """ Tests that the id is extracted from a button name with known prefix """
        button_name = f"{self.button_name_prefix}{self.button_id}"
        querydict = QueryDict(f"{button_name}=1&a=2&c=3")
        self.assertEqual(
            get_id_from_button_name(
                button_name_prefix=self.button_name_prefix, post=querydict
            ),
            self.button_id,
        )

    def test_get_no_id_from_button_name_with_wrong_prefix(self):
        """ Tests that no id is extracted from a button name with wrong prefix """
        button_name = f"wrong_prefix_{self.button_name_prefix}{self.button_id}"
        querydict = QueryDict(f"{button_name}=1&a=2&c=3")
        self.assertEqual(
            get_id_from_button_name(
                button_name_prefix=self.button_name_prefix, post=querydict
            ),
            None,
        )


class BuildFiltersTestCase(TestCase):
    """
    Tests for build_filters

    Methods
    -------
    test_build_filters_from_field_values()
        Tests that filter dictionary is build from field values
    """

    def test_build_filters_from_field_values(self):
        """ Tests that filter dictionary is build from field values """
        field_and_filter_names: List[Tuple[str, str]] = [
            ("case_number", "id"),
            ("domain", "domain__icontains"),
        ]
        fields_data: Dict[str, Any] = {
            "case_number": "42",
            "domain": "domain name",
            "unused_field": "unused value",
        }
        expected_filters = {
            "id": "42",
            "domain__icontains": "domain name",
        }
        self.assertEqual(
            build_filters(
                cleaned_data=fields_data, field_and_filter_names=field_and_filter_names
            ),
            expected_filters,
        )
