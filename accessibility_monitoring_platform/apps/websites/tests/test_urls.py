"""
Test urls of websites app
"""

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse


class LoginRequiredForWebsitesTestCase(TestCase):
    """
    Login required tests for websites

    Methods
    -------
    test_login_required_for_website_list()
        Tests websites list url redirects to login page
    test_login_required_for_website_export_list()
        Tests websites export list url redirects to login page
    """

    def test_login_required_for_website_list(self):
        """Tests websites list url redirects to login page"""
        url: str = reverse("websites:website-list")
        response: HttpResponse = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/accounts/login/?next={url}")

    def test_login_required_for_website_export_list(self):
        """Tests websites export list url redirects to login page"""
        url: str = reverse("websites:website-export-list")
        response: HttpResponse = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/accounts/login/?next={url}")
