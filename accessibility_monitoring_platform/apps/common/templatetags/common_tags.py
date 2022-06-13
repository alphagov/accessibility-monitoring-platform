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
    return f"{date_to_format:%-d %B %Y}" if date_to_format else ""


@register.filter
def gds_time(datetime_to_format: datetime) -> str:
    """Format time according to GDS style guide"""
    return f"{datetime_to_format:%-I:%M%p}".lower() if datetime_to_format else ""


@register.filter
def gds_datetime(datetime_to_format: datetime) -> str:
    """Format date and time according to GDS style guide"""
    return f"{gds_date(datetime_to_format)} {gds_time(datetime_to_format)}" if datetime_to_format else ""
