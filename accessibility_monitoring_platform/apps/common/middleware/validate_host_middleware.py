""" Check requests are for valid hosts """
import logging
import re

from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.http.request import split_domain_port, validate_host

logger = logging.getLogger(__name__)

VALID_IP_REGEX = re.compile(r"10.0\.[0-9]{1,3}\.[0-9]{1,3}")


class ValidateHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host: str = request._get_raw_host()
        domain, _ = split_domain_port(host)
        if validate_host(domain, settings.ALLOWED_HOSTS) or VALID_IP_REGEX.fullmatch(
            domain
        ):
            logger.info("Valid host found: %s", host)
        else:
            raise DisallowedHost(f"Unexpected host in request: {host}")

        response = self.get_response(request)

        return response
