"""
Utilities for report viewer app
"""

from django.http import HttpRequest

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
