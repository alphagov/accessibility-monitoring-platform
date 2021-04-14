"""
Test - query_local_website_registry forms
"""
import datetime
import pytz

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.client import RequestFactory

from ..forms import (
    AxeDataSearchForm,
    check_date_valid_or_none,
    convert_day_month_year_to_date,
)


class AxeDataSearchDomainFormTestCase(TestCase):
    """
    Form tests for axe_data

    Methods
    -------
    setUp()
        Sets up the test environment

    test_form_conforms()
        Tests if form.is_valid() is working as expected

    test_form_fails_clean_start_date_year()
        Form fails if start date is invalid

    test_form_fails_clean_end_date_year()
        Form fails if end date is invalid
    """

    def setUp(self):
        """ Sets up the test environment with a request factory """
        self.factory: RequestFactory = RequestFactory()

    def test_form_conforms(self):
        """ Tests if form.is_valid() is working as expected """
        form: AxeDataSearchForm = AxeDataSearchForm(
            data={
                "domain_name": "test",
                "start_date_day": "1",
                "start_date_month": "2",
                "start_date_year": "1900",
                "end_date_day": "3",
                "end_date_month": "4",
                "end_date_year": "2100",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(
            form.start_date == datetime.datetime(1900, 2, 1, tzinfo=pytz.UTC)
        )
        self.assertTrue(form.end_date == datetime.datetime(2100, 4, 3, tzinfo=pytz.UTC))

    def test_form_fails_clean_start_date_year(self):
        """ Tests if form.is_valid() is working as expected """
        form: AxeDataSearchForm = AxeDataSearchForm(
            data={
                "start_date_day": "31",
                "start_date_month": "2",
                "end_date_day": "1",
                "end_date_month": "1",
                "end_date_year": "2100",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors == {"start_date_year": ["This date is invalid"]})

    def test_form_fails_clean_end_date_year(self):
        """ Tests if form.is_valid() is working as expected """
        form: AxeDataSearchForm = AxeDataSearchForm(
            data={
                "start_date_day": "1",
                "start_date_month": "1",
                "start_date_year": "1900",
                "end_date_day": "31",
                "end_date_month": "2",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors == {"end_date_year": ["This date is invalid"]})


class CheckDateValidOrNoneTestCase(TestCase):
    """
    Test function check_date_valid_or_none
    """

    def test_empty_date_returns_none(self):
        day = None
        month = None
        year = None
        self.assertTrue(check_date_valid_or_none(day, month, year) is None)

    def test_valid_date_returns_none(self):
        day = "31"
        month = "12"
        year = "1999"
        self.assertTrue(check_date_valid_or_none(day, month, year) is None)

    def test_invalid_date_raises_exception(self):
        day = "30"
        month = "2"
        year = "2021"
        self.assertRaises(ValidationError, check_date_valid_or_none, day, month, year)

    def test_incomplete_date_raises_exception(self):
        day = "1"
        month = None
        year = "2021"
        self.assertRaises(ValidationError, check_date_valid_or_none, day, month, year)


class ConvertDauMonthYearToDateTestCase(TestCase):
    """
    Test function convert_day_month_year_to_date
    """

    def test_valid_date_returns_datetime(self):
        day = "31"
        month = "12"
        year = "1999"
        expected_datetime = datetime.datetime(
            year=int(year), month=int(month), day=int(day), tzinfo=pytz.UTC
        )
        self.assertTrue(
            convert_day_month_year_to_date(day, month, year) == expected_datetime
        )

    def test_invalid_date_raises_exception(self):
        day = "30"
        month = "2"
        year = "2021"
        self.assertRaises(ValueError, convert_day_month_year_to_date, day, month, year)
