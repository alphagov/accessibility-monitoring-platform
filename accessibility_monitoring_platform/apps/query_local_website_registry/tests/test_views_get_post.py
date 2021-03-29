"""
Test - query_local_website_registry views post
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import HttpResponse
from typing import (
    List,
    TypedDict,
)
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent


class DateData(TypedDict):
    start_date_day: str
    start_date_month: str
    start_date_year: str
    end_date_day: str
    end_date_month: str
    end_date_year: str


class QueryLocalViewPostTests(TestCase):
    """
    View tests for query_local_website_registry

    Methods
    -------
    setUp()
        Sets up the test environment with a user

    test_post_returns_correct_url()
        Post returns correct query string

    test_post_faulty_data()
        Redirects to empty form if bad data is entered

    test_post_correct_dates()
        Renders data if correct date data is entered

    test_post_faulty_dates_start_date_error_message_renders
        Renders error message if incorrect start date data is entered

    test_post_faulty_dates_end_date_error_message_renders
        Renders error message if incorrect end date data is entered
    """

    databases: str = '__all__'
    fixtures: List[Path] = [
        BASE_DIR / 'mocks/nuts_conversion.json',
        BASE_DIR / 'mocks/sector.json',
        BASE_DIR / 'mocks/website_reg_anon_fixture.json',
    ]

    def setUp(self):
        """ Creates a user for testing the views """
        user: User = User.objects.create(username='joe_blogs')
        user.set_password('12345')
        user.save()

    def test_post_returns_correct_url(self):
        """ Post returns correct query string """
        self.client.login(username='joe_blogs', password='12345')
        response: HttpResponse = self.client.post(
            reverse('query_local_website_registry:home'),
            data={'sector_name': 'Education'},
            follow=True
        )

        self.assertEqual(response.status_code, 200)

        self.assertRedirects(
            response,
            '/query-domains/?sector_name=Education',
            status_code=302,
            target_status_code=200,
            msg_prefix='',
            fetch_redirect_response=True
        )

    def test_post_faulty_data(self):
        self.client.login(username='joe_blogs', password='12345')
        response: HttpResponse = self.client.post(
            reverse('query_local_website_registry:home'),
            data={'bad': 'data'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(
            response,
            '/query-domains/?',
            status_code=302,
            target_status_code=200,
            msg_prefix='',
            fetch_redirect_response=True
        )

    def test_post_correct_dates(self):
        self.client.login(username='joe_blogs', password='12345')
        data: DateData = {
            'start_date_day': '1',
            'start_date_month': '1',
            'start_date_year': '2000',
            'end_date_day': '1',
            'end_date_month': '1',
            'end_date_year': '2100'
        }
        response: HttpResponse = self.client.post(
            reverse('query_local_website_registry:home'),
            data=data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(
            response,
            (
                '/query-domains/?start_date_day=1'
                '&start_date_month=1'
                '&start_date_year=2000'
                '&end_date_day=1'
                '&end_date_month=1'
                '&end_date_year=2100'
            ),
            status_code=302,
            target_status_code=200,
            msg_prefix='',
            fetch_redirect_response=True
        )

    def test_post_faulty_dates_start_date_error_message_renders(self):
        self.client.login(username='joe_blogs', password='12345')
        data: DateData = {
            'start_date_day': '31',
            'start_date_month': '2',
            'start_date_year': '2100',
            'end_date_day': '1',
            'end_date_month': '1',
            'end_date_year': '2000'
        }
        response: HttpResponse = self.client.post(
            reverse('query_local_website_registry:home'),
            data=data,
            follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This date is invalid')

    def test_post_faulty_dates_end_date_error_message_renders(self):
        self.client.login(username='joe_blogs', password='12345')
        data: DateData = {
            'start_date_day': '1',
            'start_date_month': '1',
            'start_date_year': '1900',
            'end_date_day': '31',
            'end_date_month': '2',
            'end_date_year': '2100'
        }
        response: HttpResponse = self.client.post(
            reverse('query_local_website_registry:home'),
            data=data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This date is invalid')
