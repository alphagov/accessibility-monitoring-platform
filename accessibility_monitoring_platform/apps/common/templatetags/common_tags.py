"""
Common templatetags
"""

from typing import Any, List

from django import template

register = template.Library()


@register.filter
def list_item_by_index(items: List[Any], index: int) -> Any:
    """Given a list of items and an index, return the indexed item"""
    try:
        return items[index]
    except Exception:  # pylint: disable=broad-except
        return None
