"""
Test - axe_data views
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


class FormData(TypedDict):
    domain_name: str
    start_date_day: str
    start_date_month: str
    start_date_year: str
    end_date_day: str
    end_date_month: str
    end_date_year: str


class AxeResultsHomeViewTests(TestCase):
    """
    View tests for query_local_website_registry

    Methods
    -------
    setUp()
        Sets up the test environment with a user

    test_get_returns_no_axe_test_result_headers()
        Checks get returns no Axe test result headers

    test_post_returns_axe_test_result_headers()
        Checks post returns matching Axe test result headers

    test_post_returns_paginated_axe_test_result_headers()
        Check post returns paginated Axe test result headers

    test_get_returns_specific_page()
        Check get returns no Axe test result headers

    test_get_populates_form()
        Checks get populates form from url parameters

    """

    databases: str = "__all__"
    fixtures: List[Path] = [
        BASE_DIR / "mocks/a11ymon_axe_results.json",
    ]

    def setUp(self):
        """ Creates and logs in a user for testing the views """
        user: User = User.objects.create(username="joe_blogs")
        user.set_password("12345")
        user.save()
        self.client.login(username="joe_blogs", password="12345")

    def test_get_returns_no_axe_test_result_headers(self):
        """ Get returns no Axe test result headers """
        response: HttpResponse = self.client.get(
            reverse("axe_data:home"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "test results found")

    def test_post_returns_axe_test_result_headers(self):
        """ Post returns matching Axe test result headers """
        response: HttpResponse = self.client.post(
            reverse("axe_data:home"), data={"domain_name": "Bristol"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "6 test results found")
        self.assertContains(response, "https://mybristol.bristol.ac.uk")

    def test_post_returns_paginated_axe_test_result_headers(self):
        """ Post returns paginated Axe test result headers """
        response: HttpResponse = self.client.post(
            reverse("axe_data:home"), data={"domain_name": "http"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "36 test results found")
        self.assertContains(response, "Page 1 of 2.")

    def test_get_returns_specific_page(self):
        """ Get returns no Axe test result headers """
        response: HttpResponse = self.client.get(
            reverse("axe_data:home") + "?page=2&domain_name=http",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "36 test results found")
        self.assertContains(response, "Page 2 of 2.")

    def test_get_populates_form(self):
        """ Get populates form from url parameters """
        response: HttpResponse = self.client.get(
            reverse("axe_data:home")
            + "?page=2&domain_name=bristol"
            + "&start_date_day=1&start_date_month=2&start_date_year=2000"
            + "&end_date_day=3&end_date_month=4&end_date_year=2100",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, '<input type="text" name="domain_name" value="bristol"'
        )
        self.assertContains(
            response, '<input type="number" name="start_date_day" value="1"'
        )
        self.assertContains(
            response, '<input type="number" name="start_date_month" value="2"'
        )
        self.assertContains(
            response, '<input type="number" name="start_date_year" value="2000"'
        )
        self.assertContains(
            response, '<input type="number" name="end_date_day" value="3"'
        )
        self.assertContains(
            response, '<input type="number" name="end_date_month" value="4"'
        )
        self.assertContains(
            response, '<input type="number" name="end_date_year" value="2100"'
        )

    def test_post_populates_form(self):
        data: FormData = {
            "domain_name": "bristol",
            "start_date_day": "1",
            "start_date_month": "2",
            "start_date_year": "2000",
            "end_date_day": "3",
            "end_date_month": "4",
            "end_date_year": "2100",
        }
        response: HttpResponse = self.client.post(
            reverse("axe_data:home"),
            data=data,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, '<input type="text" name="domain_name" value="bristol"'
        )
        self.assertContains(
            response, '<input type="number" name="start_date_day" value="1"'
        )
        self.assertContains(
            response, '<input type="number" name="start_date_month" value="2"'
        )
        self.assertContains(
            response, '<input type="number" name="start_date_year" value="2000"'
        )
        self.assertContains(
            response, '<input type="number" name="end_date_day" value="3"'
        )
        self.assertContains(
            response, '<input type="number" name="end_date_month" value="4"'
        )
        self.assertContains(
            response, '<input type="number" name="end_date_year" value="2100"'
        )
