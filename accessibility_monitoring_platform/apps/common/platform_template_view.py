"""
Platform template view. Used by report viewer.
"""

from typing import Any, Dict

from django.views.generic import TemplateView

from .utils import get_platform_settings


class PlatformTemplateView(TemplateView):
    """
    View of platform-level settings
    """

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add platform settings to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["platform"] = get_platform_settings()
        return context
