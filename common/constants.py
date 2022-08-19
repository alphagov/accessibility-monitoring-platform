"""
Constants used by both platform and report viewer
"""
from typing import List, Tuple

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
