"""
Common templatetags
"""

from html import escape
from typing import Any, List

import markdown

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from ..utils import undo_double_escapes  # pylint: disable=relative-beyond-top-level

register = template.Library()


@register.filter
def list_item_by_index(items: List[Any], index: int) -> Any:
    """Given a list of items and an index, return the indexed item"""
    try:
        return items[index]
    except Exception:  # pylint: disable=broad-except
        return None


@register.filter
def markdown_to_html(text: str) -> str:
    """Convert markdown text into html"""
    html: str = markdown.markdown(
        escape(text),
        extensions=settings.MARKDOWN_EXTENSIONS,
    )
    return mark_safe(undo_double_escapes(html))
