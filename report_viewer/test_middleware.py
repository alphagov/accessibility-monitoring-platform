from http import HTTPStatus

from django.test import RequestFactory, SimpleTestCase

from .middleware import RootRedirectMiddleware, ROOT_REDIRECT_DESTINATION

ROOT_PATH: str = "/"
NON_ROOT_PATH: str = "/some-path/"


class WwwRedirectMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.dummy_response = object()
        self.middleware = RootRedirectMiddleware(lambda request: self.dummy_response)

    def test_www_redirect(self):
        """Root path redirects to specific domain"""
        request = self.request_factory.get(ROOT_PATH, HTTP_HOST="www.example.com")

        response = self.middleware(request)

        self.assertEqual(response.status_code, HTTPStatus.MOVED_PERMANENTLY)
        self.assertEqual(response["Location"], ROOT_REDIRECT_DESTINATION)

    def test_non_redirect(self):
        """Non-root (anything but '/') paths do not redirect"""
        request = self.request_factory.get(NON_ROOT_PATH, HTTP_HOST="example.com")

        response = self.middleware(request)

        self.assertIs(response, self.dummy_response)
