"""
Common templatetags
"""

from datetime import date, datetime
from html import escape
from typing import TypeVar

import markdown
from django import template
from django.conf import settings
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.safestring import mark_safe

from ...cases.models import Case, CaseNoteHistory
from ..utils import (  # pylint: disable=relative-beyond-top-level
    amp_format_date,
    amp_format_datetime,
    undo_double_escapes,
)

register = template.Library()
T = TypeVar("T")


@register.filter
def list_item_by_index(items: list[T], index: int) -> T:
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


@register.filter
def amp_date(date_to_format: date) -> str:
    """Format date according to GDS style guide"""
    return amp_format_date(date_to_format)


@register.filter
def amp_datetime(datetime_to_format: datetime) -> str:
    """Format date and time according to GDS style guide"""
    if datetime_to_format:
        return amp_format_datetime(timezone.localtime(datetime_to_format))
    else:
        return ""


@register.filter
def filtered_case_note_history(
    case: Case, note_type: CaseNoteHistory.NoteType
) -> QuerySet[CaseNoteHistory]:
    """Filter case note history by note type"""
    return case.case_note_history.filter(note_type=note_type)
