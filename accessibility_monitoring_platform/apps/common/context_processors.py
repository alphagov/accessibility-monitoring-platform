"""
Context processors
"""

from typing import Dict, Union

from django.conf import settings
from django.http import HttpRequest
from django.utils import timezone

from ..common.models import FooterLink, FrequentlyUsedLink, Platform
from ..common.page_name_utils import AmpPage, get_amp_page_by_request
from ..common.utils import SessionExpiry, get_platform_settings
from ..notifications.utils import get_number_of_tasks
from .forms import AMPTopMenuForm


def platform_page(
    request: HttpRequest,
) -> Dict[str, Union[AMPTopMenuForm, str, Platform, int]]:
    """
    Populate context for template rendering. Include search form for top menu,
    name of prototype, platform settings and number of tasks.
    """
    platform: Platform = get_platform_settings()
    amp_page: AmpPage = get_amp_page_by_request(request=request)

    return {
        "today": timezone.now(),
        "session_expiry": SessionExpiry(request=request),
        "top_menu_form": AMPTopMenuForm(),
        "platform": platform,
        "number_of_tasks": get_number_of_tasks(user=request.user),
        "django_settings": settings,
        "custom_frequently_used_links": FrequentlyUsedLink.objects.filter(
            is_deleted=False
        ),
        "custom_footer_links": FooterLink.objects.filter(is_deleted=False),
        "amp_page_name": amp_page.name,
        "current_url_name": amp_page.url_name,
    }
