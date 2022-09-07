import logging

from django.utils.deprecation import MiddlewareMixin


class PeekMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def __call__(self, request):
        response = self.get_response(request)
        logging.warning("request.GET %s", request.GET)
        logging.warning("request.POST %s", request.POST)
        logging.warning("request.COOKIES %s", request.COOKIES)
        return response
