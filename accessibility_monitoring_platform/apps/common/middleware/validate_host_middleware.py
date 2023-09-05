""" Check requests are for valid hosts """
import logging

from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ValidateHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host: str = request.get_host()
        if host.startswith("localhost") or host.startswith("10.0."):
            logger.info("Expected host %s", host)
        else:
            raise ValidationError(f"Unexpected host in request: {host}")

        response = self.get_response(request)

        return response
