"""
Test - query_local_website_registry forms
"""
from django.test import TestCase
from ..forms import AxeDataSearchForm
from django.test.client import RequestFactory


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
                "start_date_month": "1",
                "start_date_year": "1900",
                "end_date_day": "1",
                "end_date_month": "1",
                "end_date_year": "2100",
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_fails_clean_start_date_year(self):
        """ Tests if form.is_valid() is working as expected """
        form: AxeDataSearchForm = AxeDataSearchForm(
            data={
                "start_date_day": "31",
                "start_date_month": "2",
                "start_date_year": "1900",
                "end_date_day": "1",
                "end_date_month": "1",
                "end_date_year": "2100",
            }
        )
        self.assertFalse(form.is_valid())

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
