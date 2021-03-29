"""
Test - query_local_website_registry get
"""
from django.test import TestCase
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.models import User
from pathlib import Path
from typing import List
BASE_DIR = Path(__file__).resolve().parent


class QueryLocalViewTests(TestCase):
    """
    View tests for query_local_website_registry

    Methods
    -------
    setUp()
        Sets up the test environment with a user

    test_home_page_loads_correctly()
        Tests if a user is logged in and can access the query_local_website_registry

    test_query_loads_table()
        String query loads table correctly

    test_query_returns_empty_table()
        Returns an empty table if query is empty

    test_error_messages_render
        Returns an empty table if query is empty
    """
    databases: str = '__all__'
    fixtures: List[Path] = [
        BASE_DIR / 'mocks/nuts_conversion.json',
        BASE_DIR / 'mocks/sector.json',
        BASE_DIR / 'mocks/website_reg_anon_fixture.json',
    ]

    def setUp(self):
        """ Creates a user for testing the views """
        user: User = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()

    def test_home_page_loads_correctly(self):
        """ Tests if a user is logged in and can access the query_local_website_registry """
        self.client.login(username='testuser', password='12345')
        response: HttpResponse = self.client.get(reverse('query_local_website_registry:home'), follow=True)
        self.assertEqual(str(response.context['user']), 'testuser')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Query Domain Register')

    def test_query_loads_table(self):
        """ String query loads table correctly """
        url_req: str = f"{reverse('query_local_website_registry:home')}?sector_name=Education"
        self.client.login(username='testuser', password='12345')
        response: HttpResponse = self.client.get(url_req, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'http://www.webite.co.uk/')
        self.assertContains(response, 'http://www.website1.co.uk/')

    def test_query_returns_empty_table(self):
        """ Returns an empty table if query is empty """
        url_req: str = f"{reverse('query_local_website_registry:home')}?"
        self.client.login(username='testuser', password='12345')
        response: HttpResponse = self.client.get(url_req, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Query Domain Register')
        self.assertFalse('Education' in response)

    def test_no_is_shown_with_empty_query(self):
        """ Returns an empty table if query is empty """
        url_req: str = f"{reverse('query_local_website_registry:home')}?"
        self.client.login(username='testuser', password='12345')
        response: HttpResponse = self.client.get(url_req, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Query Domain Register')
        self.assertFalse('Education' in response)
