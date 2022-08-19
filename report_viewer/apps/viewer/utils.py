"""
Utilities for report viewer app
"""

from typing import List, Tuple

from django.http import HttpRequest

PLATFORM_VIEWER_DOMAINS: List[Tuple[str, str]] = [
    ("localhost:8081", "localhost:8082"),  # Used for local development
    ("localhost:8001", "localhost:8002"),  # Used for automated testing
    (
        "accessibility-monitoring-platform-test.london.cloudapps.digital",
        "accessibility-monitoring-report-viewer-test.london.cloudapps.digital",
    ),
    (
        "accessibility-monitoring-platform-production.london.cloudapps.digital",
        "accessibility-monitoring-report-viewer-production.london.cloudapps.digital",
    ),
    (
        "platform-test.accessibility-monitoring.service.gov.uk",
        "reports-test.accessibility-monitoring.service.gov.uk",
    ),
    (
        "platform.accessibility-monitoring.service.gov.uk",
        "reports.accessibility-monitoring.service.gov.uk",
    ),
]


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
