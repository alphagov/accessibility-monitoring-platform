"""
Tests for view - dashboard
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import HttpResponse


class DashboardViewTests(TestCase):
    """
    View tests for dashboard

    Methods
    -------
    setUp()
        Sets up the test environment

    test_dashboard_loads_correctly_with_auth()
        Tests dashboard with authentication

    test_dashboard_loads_correctly_no_auth()
        Tests dashboard with no authentication
    """

    def setUp(self):
        """ Creates a user for testing the views """
        user: User = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()

    def test_dashboard_loads_correctly_with_auth(self):
        """ Tests if a user is logged in and can access the Dashboard """
        self.client.login(username="testuser", password="12345")
        response: HttpResponse = self.client.get(reverse("dashboard:home"))
        self.assertEqual(str(response.context["user"]), "testuser")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_dashboard_loads_correctly_no_auth(self):
        """ Tests if a unauthenticated user returns a 302 response """
        response: HttpResponse = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)
