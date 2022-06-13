"""
Common templatetags
"""

from datetime import date, datetime
from html import escape
from typing import Any, List

import markdown

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from ..utils import (  # pylint: disable=relative-beyond-top-level
    format_gds_date,
    format_gds_datetime,
    format_gds_time,
)

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
    return mark_safe(
        markdown.markdown(
            escape(text),
            extensions=settings.MARKDOWN_EXTENSIONS,
        )
    )


@register.filter
def gds_date(date_to_format: date) -> str:
    """Format date according to GDS style guide"""
    return format_gds_date(date_to_format)


@register.filter
def gds_time(datetime_to_format: datetime) -> str:
    """Format time according to GDS style guide"""
    return format_gds_time(datetime_to_format)


@register.filter
def gds_datetime(datetime_to_format: datetime) -> str:
    """Format date and time according to GDS style guide"""
    return format_gds_datetime(datetime_to_format)
