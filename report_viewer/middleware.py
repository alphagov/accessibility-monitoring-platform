"""
Middleware for report viewer
"""
from django.http import HttpResponsePermanentRedirect

ROOT_REDIRECT_DESTINATION = "http://www.accessibility-monitoring.service.gov.uk/"


class RootRedirectMiddleware:
    """
    When request is for root then redirect to http://www.accessibility-monitoring.service.gov.uk/
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.path == "/":
            return HttpResponsePermanentRedirect(ROOT_REDIRECT_DESTINATION)
        else:
            return self.get_response(request)
