"""
Tests for utility functions in websites app
"""
from django.test import TestCase

from django.contrib.auth.models import User

from ..utils import get_list_of_nuts318_codes
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent


class WebsitesUtilsTests(TestCase):
    """
    Tests for utility functions of websites app

    Methods
    -------

    setUp()
        Sets up the test environment with a user

    test_get_list_of_nuts318_codes()
        Tests whether search query returns a list of nuts118 codes
    """

    databases: str = "__all__"
    fixtures: List[Path] = [
        BASE_DIR / "mocks/nuts_conversion.json",
    ]

    def setUp(self):
        """Creates a user for testing the views"""
        user: User = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()

    def test_get_list_of_nuts318_codes(self):
        """Tests whether search query returns a list of nuts118 codes"""
        res: List[str] = list(get_list_of_nuts318_codes("Lewisham"))
        expected_result: List[str] = ["UKI44"]
        self.assertEqual(res, expected_result)
