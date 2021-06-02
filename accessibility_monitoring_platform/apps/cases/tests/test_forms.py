"""
Test - cases forms
"""
from datetime import datetime
import pytz

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.client import RequestFactory

from ..forms import (
    StringOrNone,
    DateRangeForm,
    SearchForm,
    check_date_valid_or_none,
    convert_day_month_year_to_date,
)


class DateRangeFormTestCase(TestCase):
    """
    Form tests for date ranges

    Methods
    -------
    setUp()
        Sets up the test environment

    test_form_validation()
        Tests if form.is_valid() is working as expected

    test_form_fails_clean_start_date_year()
        Form fails if start date is invalid

    test_form_fails_clean_end_date_year()
        Form fails if end date is invalid
    """

    def setUp(self):
        """ Sets up the test environment with a request factory """
        self.factory: RequestFactory = RequestFactory()

    def test_form_validation(self):
        """ Tests if form.is_valid() is working as expected """
        form: DateRangeForm = DateRangeForm(
            data={
                "start_date_day": "1",
                "start_date_month": "2",
                "start_date_year": "1900",
                "end_date_day": "3",
                "end_date_month": "4",
                "end_date_year": "2100",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.start_date == datetime(1900, 2, 1, tzinfo=pytz.UTC))
        self.assertTrue(form.end_date == datetime(2100, 4, 3, tzinfo=pytz.UTC))

    def test_form_fails_clean_start_date_year(self):
        """ Tests if form.is_valid() is working as expected """
        form: DateRangeForm = DateRangeForm(
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
        form: DateRangeForm = DateRangeForm(
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


class SearchFormTestCase(TestCase):
    """
    Form tests for cases

    Methods
    -------
    setUp()
        Sets up the test environment

    test_amp_field_rendering()
        Tests AMP fields have been rendered as expected

    test_form_validation()
        Tests if form.is_valid() is working as expected

    test_form_fails_clean_start_date_year()
        Form fails if start date is invalid

    test_form_fails_clean_end_date_year()
        Form fails if end date is invalid
    """

    def setUp(self):
        """ Sets up the test environment with a request factory """
        self.factory: RequestFactory = RequestFactory()

    def test_amp_field_rendering(self):
        """ Tests AMP fields have been rendered as expected """
        form: SearchForm = SearchForm()
        rendered_form: str = str(form)

        # AMPCharFields
        self.assertIn('<label for="id_case_number">Case number:</label>', rendered_form)
        self.assertIn(
            '<input type="text" name="case_number" class="govuk-input govuk-input--width-10"'
            ' maxlength="100" id="id_case_number">',
            rendered_form,
        )
        self.assertIn('<label for="id_domain">Domain:</label>', rendered_form)
        self.assertIn(
            '<input type="text" name="domain" class="govuk-input govuk-input--width-10"'
            ' maxlength="100" id="id_domain">',
            rendered_form,
        )
        self.assertIn(
            '<label for="id_organisation">Organisation:</label>', rendered_form
        )
        self.assertIn(
            '<input type="text" name="organisation" class="govuk-input govuk-input--width-10"'
            ' maxlength="100" id="id_organisation">',
            rendered_form,
        )

        # AMPChoiceFields
        self.assertIn('<label for="id_sort_by">Sort by:</label>', rendered_form)
        self.assertIn(
            '<select name="sort_by" class="govuk-select" id="id_sort_by">',
            rendered_form,
        )
        self.assertIn('<label for="id_auditor">Auditor:</label>', rendered_form)
        self.assertIn(
            '<select name="auditor" class="govuk-select" id="id_auditor">',
            rendered_form,
        )
        self.assertIn('<label for="id_status">Status:</label>', rendered_form)
        self.assertIn(
            '<select name="status" class="govuk-select" id="id_status">',
            rendered_form,
        )

    def test_form_validation(self):
        """ Tests if form.is_valid() is working as expected """
        form: SearchForm = SearchForm(
            data={
                "case_number": "42",
                "domain": "test_domain",
                "organisation": "test_organiation",
                "auditor": "Andrew Hick",
                "status": "new-case",
                "organisation": "test",
                "start_date_day": "1",
                "start_date_month": "1",
                "start_date_year": "1900",
                "end_date_day": "1",
                "end_date_month": "1",
                "end_date_year": "2100",
                "sort_by": "-id",
            }
        )
        self.assertTrue(form.is_valid())


class CheckDateValidOrNoneTestCase(TestCase):
    """
    Test function check_date_valid_or_none

    test_empty_date_returns_none():
        Test empty date returns none

    test_valid_date_returns_none():
        Test valid date returns none

    test_invalid_date_raises_exception():
        Test invalid date raises a ValidationError exception

    test_incomplete_date_raises_exception():
        Test incomplete date raises a ValidationError exception
    """

    def test_empty_date_returns_none(self):
        """ Test empty date returns none """
        day: StringOrNone = None
        month: StringOrNone = None
        year: StringOrNone = None
        self.assertTrue(check_date_valid_or_none(day, month, year) is None)

    def test_valid_date_returns_none(self):
        """ Test valid date returns none """
        day: StringOrNone = "31"
        month: StringOrNone = "12"
        year: StringOrNone = "1999"
        self.assertTrue(check_date_valid_or_none(day, month, year) is None)

    def test_invalid_date_raises_exception(self):
        """ Test invalid date raises a ValidationError exception """
        day: StringOrNone = "30"
        month: StringOrNone = "2"
        year: StringOrNone = "2021"
        self.assertRaises(ValidationError, check_date_valid_or_none, day, month, year)

    def test_incomplete_date_raises_exception(self):
        """ Test incomplete date raises a ValidationError exception """
        day: StringOrNone = "1"
        month: StringOrNone = None
        year: StringOrNone = "2021"
        self.assertRaises(ValidationError, check_date_valid_or_none, day, month, year)


class ConvertDayMonthYearToDateTestCase(TestCase):
    """
    Test function convert_day_month_year_to_date

    test_valid_date_returns_datetime():
        Test valid date returns datetime

    test_invalid_date_raises_exception():
        Test invalid date raises exception
    """

    def test_valid_date_returns_datetime(self):
        """ Test valid date returns datetime """
        day: str = "31"
        month: str = "12"
        year: str = "1999"
        expected_datetime: datetime = datetime(
            year=int(year), month=int(month), day=int(day), tzinfo=pytz.UTC
        )
        self.assertTrue(
            convert_day_month_year_to_date(day, month, year) == expected_datetime
        )

    def test_invalid_date_raises_exception(self):
        """ Test invalid date raises exception """
        day: str = "30"
        month: str = "2"
        year: str = "2021"
        self.assertRaises(ValueError, convert_day_month_year_to_date, day, month, year)
