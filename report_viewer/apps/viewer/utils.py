"""
Utilities for report viewer app
"""

from typing import Dict

import requests

from django.http import Http404, HttpRequest

from rest_framework.authtoken.models import Token

from common.constants import PLATFORM_VIEWER_DOMAINS


def get_platform_domain(request: HttpRequest) -> str:
    """Derive platform's domain name from that of the report viewer in a request"""
    domain_name: str = request.META["HTTP_HOST"] if "HTTP_HOST" in request.META else ""
    if domain_name:
        for platform_domain, viewer_domain in PLATFORM_VIEWER_DOMAINS:
            if viewer_domain in domain_name:
                return platform_domain
        return domain_name.replace("-report-viewer.", ".")
    else:
        return ""


def get_s3_report(guid: str, request: HttpRequest) -> Dict[str, str]:
    """Get S3Report data from platform api"""
    token: Token = Token.objects.all()[0]
    headers = {"Authorization": f"Token {token.key}"}
    platform_domain: str = get_platform_domain(request)
    protocol: str = "http://" if "localhost" in platform_domain else "https://"
    s3_report_response: requests.models.Response = requests.get(
        f"{protocol}{platform_domain}/api/v1/s3-reports/{guid}/",
        headers=headers,
    )
    if s3_report_response.status_code >= 400:
        raise Http404
    return s3_report_response.json()
