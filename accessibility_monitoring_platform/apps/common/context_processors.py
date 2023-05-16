"""
Context processors
"""
from typing import Dict, Union

from django.conf import settings
from django.http import HttpRequest
from django.utils import timezone

from ..common.models import FrequentlyUsedLink, Platform
from ..common.utils import get_platform_settings
from ..notifications.models import Notification
from ..reminders.utils import get_number_of_reminders_for_user
from ..overdue.utils import get_overdue_cases
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
        "number_of_notifications": Notification.objects.filter(
            user=request.user, read=False
        ).count(),
        "number_of_reminders": get_number_of_reminders_for_user(user=request.user),
        "number_of_overdue": len(get_overdue_cases(user_request=request.user) or []),
        "django_settings": settings,
        "custom_frequently_used_links": FrequentlyUsedLink.objects.filter(
            is_deleted=False
        ),
    }
