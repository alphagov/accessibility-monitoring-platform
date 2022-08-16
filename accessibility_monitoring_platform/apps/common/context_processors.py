"""
Context processors
"""
from typing import Dict, List, Union

from django.http import HttpRequest

from ..common.models import Platform
from ..common.utils import get_platform_settings
from ..reminders.utils import get_number_of_reminders_for_user
from ..reports.utils import get_report_viewer_url_prefix
from ..overdue.utils import get_overdue_cases
from .forms import AMPTopMenuForm

NON_PROTOTYPE_DOMAINS: List[str] = [
    "localhost",
    "accessibility-monitoring-platform-production.london.cloudapps.digital",
    "accessibility-monitoring-platform-test.london.cloudapps.digital",
    "platform.accessibility-monitoring.service.gov.uk",
]


def platform_page(
    request: HttpRequest,
) -> Dict[str, Union[AMPTopMenuForm, str, Platform, int]]:
    """
    Populate context for template rendering. Include search form for top menu,
    name of prototype, platform settings and number of reminders.
    """
    absolute_uri: str = request.build_absolute_uri()
    if any(
        [
            non_prototype_domain in absolute_uri
            for non_prototype_domain in NON_PROTOTYPE_DOMAINS
        ]
    ):
        prototype_name: str = ""
    else:
        prototype_name: str = (
            absolute_uri.split(".")[0].replace("https://", "").replace("http://", "")
        )

    platform: Platform = get_platform_settings()

    return {
        "top_menu_form": AMPTopMenuForm(),
        "prototype_name": prototype_name,
        "platform": platform,
        "number_of_reminders": get_number_of_reminders_for_user(user=request.user),  # type: ignore
        "number_of_overdue": len(get_overdue_cases(user_request=request.user) or []),  # type: ignore
        "report_viewer_url_prefix": get_report_viewer_url_prefix(request=request),
    }
