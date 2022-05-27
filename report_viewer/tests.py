from http import HTTPStatus

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase

from .middleware import RootRedirectMiddleware, ROOT_REDIRECT_DESTINATION

ROOT_PATH: str = "/"
NON_ROOT_PATH: str = "/some-path/"


class RootRedirectMiddlewareTests(SimpleTestCase):
    """
    Test that middleware redirects when path is root ('/').
    """

    def setUp(self):
        self.request_factory = RequestFactory()
        self.dummy_response = object()
        self.middleware = RootRedirectMiddleware(lambda request: self.dummy_response)

    def test_www_redirect(self):
        """Root path redirects to specific domain"""
        response: HttpResponse = self.middleware(
            self.request_factory.get(ROOT_PATH, HTTP_HOST="www.example.com")
        )

        self.assertEqual(response.status_code, HTTPStatus.MOVED_PERMANENTLY)
        self.assertEqual(response["Location"], ROOT_REDIRECT_DESTINATION)

    def test_non_redirect(self):
        """Non-root (anything but '/') paths do not redirect"""
        response: HttpResponse = self.middleware(
            self.request_factory.get(NON_ROOT_PATH, HTTP_HOST="example.com")
        )

        self.assertIs(response, self.dummy_response)


class HealthcheckViewTest(TestCase):
    """
    Test that the healthcheck endpoint is working
    """

    def test_healthcheck_url_works(self):
        """Test athat the healthcheck endpoint responds correctly"""
        response = self.client.get("/healthcheck/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"healthcheck": "ok"})
