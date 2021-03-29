"""
Test - query_local_website_registry view helpers
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.http import HttpResponse
from ..views import (
    date_fixer,
    get_list_of_nuts118
)
import csv
import datetime
import io
from pathlib import Path
import pytz
from typing import (
    Any,
    List,
)
BASE_DIR = Path(__file__).resolve().parent


class QueryLocalHelpersTests(TestCase):
    """
    View tests for helper functions - query_local_website_registry

    Methods
    -------
    setUp()
        Sets up the test environment with a user

    test_download_as_csv()
        Tests whether the download function returns a CSV

    test_get_list_of_nuts118()
        Tests whether search query returns a list of nuts118 codes

    def test_date_fixer(self):
        Tests whether the date fixer returns a valid date

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

    def test_download_as_csv(self):
        """ Tests whether the download function returns a CSV """
        self.client.login(username='testuser', password='12345')
        response: HttpResponse = self.client.get(
            '/query-domains/?sector_name=Education&format=csv',
            follow=True
        )
        self.assertEqual(response.status_code, 200)

        content: str = response.content.decode('utf-8')
        cvs_reader: Any = csv.reader(io.StringIO(content))
        body: List[str] = list(cvs_reader)
        header: str = body.pop(0)
        self.assertEqual(
            header,
            [
                'service',
                'sector',
                'last_updated',
                'url',
                'domain',
                'html_title',
                'nuts3'
            ]
        )
        self.assertEqual(len(body), 6)

    def test_get_list_of_nuts118(self):
        """ Tests whether search query returns a list of nuts118 codes """
        res: Any = get_list_of_nuts118('Lewisham')
        expected_result: List[str] = ['UKI44']
        self.assertEqual(res, expected_result)

    def test_date_fixer(self):
        """ Tests whether the date fixer returns a valid date """
        res: datetime.datetime = date_fixer('2000', '1', '1', True)
        expected_result: datetime.datetime = datetime.datetime(
            year=2000,
            month=1,
            day=1,
            tzinfo=pytz.UTC
        )
        self.assertEqual(res, expected_result)

        res: datetime.datetime = date_fixer('', '', '', True)
        expected_result: datetime.datetime = datetime.datetime(
            year=2100,
            month=1,
            day=1,
            tzinfo=pytz.UTC
        )
        self.assertEqual(res, expected_result)

        res: datetime.datetime = date_fixer('', '', '', False)
        expected_result: datetime.datetime = datetime.datetime(
            year=1900,
            month=1,
            day=1,
            tzinfo=pytz.UTC
        )
        self.assertEqual(res, expected_result)
