"""
Context processors
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from django.conf import LazySettings, settings
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils import timezone

from ..cases.models import BaseCase
from ..common.models import FooterLink, FrequentlyUsedLink, Platform
from ..common.sitemap import Sitemap
from ..common.utils import SessionExpiry, get_platform_settings
from ..notifications.utils import get_number_of_tasks
from .forms import AMPTopMenuForm


@dataclass
class PlatformPageContext:
    today: datetime
    session_expiry: SessionExpiry
    top_menu_form: AMPTopMenuForm
    platform: Platform
    number_of_tasks: int
    django_settings: LazySettings
    frequently_used_links: QuerySet[FrequentlyUsedLink]
    custom_footer_links: QuerySet[FooterLink]
    sitemap: Sitemap
    case: BaseCase | None


def platform_page(
    request: HttpRequest,
) -> dict[str, Any]:
    """
    Populate context for template rendering. Include search form for top menu,
    name of prototype, platform settings and number of tasks.
    """
    platform: Platform = get_platform_settings()
    sitemap: Sitemap = Sitemap(request=request)

    return asdict(
        PlatformPageContext(
            today=timezone.now(),
            session_expiry=SessionExpiry(request=request),
            top_menu_form=AMPTopMenuForm(),
            platform=platform,
            number_of_tasks=get_number_of_tasks(user=request.user),
            django_settings=settings,
            frequently_used_links=FrequentlyUsedLink.objects.filter(is_deleted=False),
            custom_footer_links=FooterLink.objects.filter(is_deleted=False),
            sitemap=sitemap,
            case=sitemap.current_platform_page.get_case(),
        )
    )
