"""
Tests for views in websites app
"""

from pathlib import Path
from typing import List

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from ..forms import DEFAULT_SORT

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
    test_query_returns_empty_table()
        Returns an empty table if query is empty
    test_error_messages_render
        Show error message if invalid data is entered
    """

    databases: str = "__all__"
    fixtures: List[Path] = [
        BASE_DIR / "mocks/nuts_conversion.json",
        BASE_DIR / "mocks/sector.json",
        BASE_DIR / "mocks/website_reg_anon_fixture.json",
    ]

    def setUp(self):
        """ Creates a user and logs in to access the views """
        user: User = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        self.client.login(username="testuser", password="12345")

    def test_home_page_loads_correctly(self):
        """ Tests if a user is logged in and can access the query_local_website_registry """
        response: HttpResponse = self.client.get(
            reverse("websites:website-list"), follow=True
        )
        self.assertEqual(str(response.context["user"]), "testuser")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Query Domain Register")

    def test_query_loads_table(self):
        """ String query loads table correctly """
        url_req: str = f"{reverse('websites:website-list')}?sector=9&sort_by={DEFAULT_SORT}"
        response: HttpResponse = self.client.get(url_req, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "http://www.webite.co.uk/")
        self.assertContains(response, "http://www.website1.co.uk/")

    def test_query_returns_empty_table(self):
        """ Returns an empty table if query is empty """
        url_req: str = f"{reverse('websites:website-list')}?"
        response: HttpResponse = self.client.get(url_req, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Query Domain Register")
        self.assertFalse("Education" in response)

    def test_error_is_shown_with_bad_date_entered(self):
        """ Returns an empty table and shows an error message if a bad date is entered """
        url_req: str = f"{reverse('websites:website-list')}?start_date_0=30&start_date_1=2&start_date_2=2020"
        response: HttpResponse = self.client.get(url_req, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Query Domain Register")
        self.assertFalse("Education" in response)
        self.assertContains(response, "Enter a valid date.")
