from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import User, AnonymousUser
from django.utils import timezone
from django.urls import reverse
from django.test.client import RequestFactory, Client

from accessibility_monitoring_platform.apps.dashboard.views import home


class QuestionIndexViewTests(TestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
    #     self.user = User.objects.create_user(
    #         username='jacob',
    #         email='jacob@…',
    #         password='top_secret'
    #     )

    def test_wrong_uri_returns_404(self):
        response = self.client.get('/something/really/weird/')
        self.assertEqual(response.status_code, 404)

    def test_no_notes(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        request = self.factory.get('dashboard:home')

        response = home(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This is the dashboard')
