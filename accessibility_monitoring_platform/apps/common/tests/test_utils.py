"""
Test - query_local_website_registry view helpers
"""
import csv
import io
from typing import Any, List

from django.db import models
from django.http import HttpResponse
from django.test import TestCase

from ..utils import download_as_csv, extract_domain_from_url


class MockModel(models.Model):
    integer_field = models.IntegerField()
    char_field = models.CharField(max_length=9)
    field_not_in_csv = models.IntegerField(null=True)


MOCK_MODEL_FIELDS = ["integer_field", "char_field"]
MOCK_MODEL_DATA = [['1', 'char1'], ['2', 'char2']]
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
            f"attachment; filename={CSV_FILENAME}")

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
    setUp()
        Sets up the test environment with a call to download_as_csv

    test_response_code_is_200()
        Tests whether the download function response has status code 200

    test_csv_header_is_as_expected()
        Tests that the csv header matches the list of fields

    test_csv_body_is_as_expected()
        Tests that the csv data matches that returned by the queryset
    """

    def test_extract_domain_from_url_https(self):
        """ Tests that the domain is extracted from a url with https protocol """
        self.assertEqual(extract_domain_from_url("https://example.com/index.html"), "example.com")

    def test_extract_domain_from_url_http(self):
        """ Tests that the domain is extracted from a url with http protocol """
        self.assertEqual(extract_domain_from_url("http://example.com"), "example.com")

    def test_extract_domain_from_url_no_protocol(self):
        """ Tests that the domain is not extracted from a url with no protocol """
        self.assertEqual(extract_domain_from_url("example.com"), "")