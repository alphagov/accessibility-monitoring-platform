"""
Tests for views in websites app
"""
from datetime import timedelta
from pathlib import Path
from typing import List

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from ...common.forms import DEFAULT_START_DATE, DEFAULT_END_DATE
from ..forms import DEFAULT_SORT
from ..views import check_only_default_date_filters_applied

BASE_DIR = Path(__file__).resolve().parent


class QueryLocalViewTests(TestCase):
    """
    View tests for websites

    Methods
    -------
    setUp()
        Sets up the test environment with a user
    test_home_page_loads_correctly()
        Tests if a user is logged in and can access the list of websites
    test_query_loads_table()
        String query loads table correctly
    test_query_returns_no_table_for_empty_query()
        Returns an no table if query is empty
    test_query_returns_no_table_for_only_default_date_range()
        Returns an no table if query is only default start and end dates
    test_query_returns_no_table_for_non_existant_location()
        Returns an no table if query has location with mo matching nuts code
    test_error_is_shown_with_bad_date_entered()
        Returns an no table and shows an error message if a bad date is entered
    """

    databases: str = "__all__"
    fixtures: List[Path] = [
        BASE_DIR / "mocks/nuts_conversion.json",
        BASE_DIR / "mocks/sector.json",
        BASE_DIR / "mocks/website_reg_anon_fixture.json",
    ]

    def setUp(self):
        """Creates a user and logs in to access the views"""
        user: User = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        self.client.login(username="testuser", password="12345")

    def test_home_page_loads_correctly(self):
        """Tests if a user is logged in and can access the query_local_website_registry"""
        response: HttpResponse = self.client.get(
            reverse("websites:website-list"), follow=True
        )
        self.assertEqual(str(response.context["user"]), "testuser")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Query domain register")

    def test_query_loads_table(self):
        """String query loads table correctly"""
        url_req: str = (
            f"{reverse('websites:website-list')}?sector=9&sort_by={DEFAULT_SORT}"
        )
        response: HttpResponse = self.client.get(url_req, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "http://www.webite.co.uk/")
        self.assertContains(response, "http://www.website1.co.uk/")

    def test_query_returns_no_table_for_empty_query(self):
        """Returns an no table if query is empty"""
        url_req: str = f"{reverse('websites:website-list')}?"
        response: HttpResponse = self.client.get(url_req, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Query domain register")
        self.assertFalse("URL" in response)

    def test_query_returns_no_table_for_only_default_date_range(self):
        """Returns an no table if query is only default start and end dates"""
        url_req: str = f"{reverse('websites:website-list')}?start_date_0=&start_date_1=&start_date_2=&end_date_0=&end_date_1=&end_date_2="
        response: HttpResponse = self.client.get(url_req, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Query domain register")
        self.assertFalse("URL" in response)

    def test_query_returns_no_table_for_non_existant_location(self):
        """Returns an no table if query has location with mo matching nuts code"""
        url_req: str = f"{reverse('websites:website-list')}?location=narnia"
        response: HttpResponse = self.client.get(url_req, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Query domain register")
        self.assertFalse("URL" in response)

    def test_error_is_shown_with_bad_date_entered(self):
        """Returns an no table and shows an error message if a bad date is entered"""
        url_req: str = f"{reverse('websites:website-list')}?start_date_0=30&start_date_1=2&start_date_2=2020"
        response: HttpResponse = self.client.get(url_req, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Query domain register")
        self.assertFalse("URL" in response)
        self.assertContains(response, "Enter a valid date.")


class CheckOnlyDefaultDateFiltersAppliedTestCase(TestCase):
    """
    Test check_only_default_date_filters_applied returns true
    only if default date range and no other in filters.

    Methods
    -------
    setUp()
        Populates filters dictionary
    test_check_only_default_date_filters_applied()
        Test check_only_default_date_filters_applied returns True if only default date range in filters
    test_check_only_default_date_filters_applied_different_date_range()
        Test check_only_default_date_filters_applied returns false if a different date range in filters
    test_check_only_default_date_filters_applied_additional_filters()
        Test check_only_default_date_filters_applied returns false if a additional filters
    """

    def setUp(self):
        """Populate filters dictionary"""
        self.filters = {
            "last_updated__gte": DEFAULT_START_DATE,
            "last_updated__lte": DEFAULT_END_DATE,
        }

    def test_check_only_default_date_filters_applied(self):
        """
        Test check_only_default_date_filters_applied returns true if only default date range in filters
        """
        self.assertTrue(check_only_default_date_filters_applied(self.filters))

    def test_check_only_default_date_filters_applied_different_date_range(self):
        """
        Test check_only_default_date_filters_applied returns false if a different date range in filters
        """
        self.filters["last_updated__gte"] = DEFAULT_START_DATE + timedelta(days=1)
        self.assertFalse(check_only_default_date_filters_applied(self.filters))

    def test_check_only_default_date_filters_applied_additional_filters(self):
        """
        Test check_only_default_date_filters_applied returns false if a additional filters
        """
        self.filters["any_other_key"] = None
        self.assertFalse(check_only_default_date_filters_applied(self.filters))
