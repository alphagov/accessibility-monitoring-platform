"""
Context processors
"""

from typing import Dict, Union

from django.conf import settings
from django.http import HttpRequest
from django.utils import timezone

from ..cases.utils import get_post_case_alerts_count
from ..common.models import FooterLink, FrequentlyUsedLink, Platform
from ..common.utils import get_platform_settings
from ..notifications.utils import (
    get_number_of_tasks,
    get_number_of_unread_notifications,
)
from .forms import AMPTopMenuForm


def platform_page(
    request: HttpRequest,
) -> Dict[str, Union[AMPTopMenuForm, str, Platform, int]]:
    """
    Populate context for template rendering. Include search form for top menu,
    name of prototype, platform settings and number of reminders.
    """
    platform: Platform = get_platform_settings()

    return {
        "today": timezone.now(),
        "top_menu_form": AMPTopMenuForm(),
        "platform": platform,
        "number_of_unread_notifications": get_number_of_unread_notifications(
            user=request.user
        ),
        "number_of_tasks": get_number_of_tasks(user=request.user),
        "django_settings": settings,
        "custom_frequently_used_links": FrequentlyUsedLink.objects.filter(
            is_deleted=False
        ),
        "custom_footer_links": FooterLink.objects.filter(is_deleted=False),
        "post_case_alerts_count": get_post_case_alerts_count(user=request.user),
    }
