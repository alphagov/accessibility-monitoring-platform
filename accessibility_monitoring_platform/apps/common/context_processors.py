"""
Context processors
"""
import re
from typing import Dict, Union

from ..audits.models import Audit
from ..cases.models import Case
from ..common.models import Platform
from ..common.utils import get_platform_settings
from ..reminders.utils import get_number_of_reminders_for_user

from .forms import AMPTopMenuForm


def platform_page(
    request,
) -> Dict[str, Union[int, str, AMPTopMenuForm, Platform, Case, None]]:
    """
    Lookup the page title using URL path and place it in context for template rendering.
    Also include search form for top menu, name of prototype and platform settings.
    """
    url_without_id = re.sub(r"\d+", "[id]", request.path)

    case: Union[Case, None] = None
    if url_without_id.startswith("/cases/[id]/"):
        try:
            case = Case.objects.get(id=request.path.split("/")[2])
        except Case.DoesNotExist:
            pass
    elif url_without_id.startswith("/audits/[id]/"):
        try:
            audit: Audit = Audit.objects.get(id=request.path.split("/")[2])
            case = audit.case
        except Audit.DoesNotExist:
            pass

    absolute_uri: str = request.build_absolute_uri()
    if (
        "localhost" in absolute_uri
        or "accessibility-monitoring-platform-production.london.cloudapps.digital"
        in absolute_uri
        or "accessibility-monitoring-platform-test.london.cloudapps.digital"
        in absolute_uri
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
        "case": case,
        "number_of_reminders": get_number_of_reminders_for_user(user=request.user),
    }
