"""
Common templatetags
"""

from html import escape
from typing import Any, List

import markdown

from django import template
from django.utils.safestring import mark_safe

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
    return mark_safe(markdown.markdown(escape(text)))
