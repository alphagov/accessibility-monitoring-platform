"""Test healthcheck endpoint"""
from django.test import TestCase


class HealthcheckViewTest(TestCase):
    """
    Test that the healthcheck endpoint is working
    """

    def test_healthcheck_url_works(self):
        """Test athat the healthcheck endpoint responds correctly"""
        response = self.client.get("/healthcheck/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"healthcheck": "ok"})
