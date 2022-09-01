"""
Context processors
"""
from typing import Dict, Union

from django.conf import settings
from django.http import HttpRequest

from ..common.models import Platform
from ..common.utils import get_platform_settings
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
        "top_menu_form": AMPTopMenuForm(),
        "platform": platform,
        "number_of_reminders": get_number_of_reminders_for_user(user=request.user),  # type: ignore
        "number_of_overdue": len(get_overdue_cases(user_request=request.user) or []),  # type: ignore
        "django_settings": settings,
    }
