"""Utilities to build JSON serialisable object to store in Case.archive"""

from datetime import date, datetime
from typing import Any

from .templatetags.common_tags import amp_date, amp_datetime


def build_section(
    name: str,
    complete_date: date | datetime | None,
    fields: list[dict[str, str | None]],
    subsections: list[dict[str, str | None]] | None = None,
):
    complete_flag = complete_date.isoformat() if complete_date else None
    return {
        "name": name,
        "complete": complete_flag,
        "fields": fields,
        "subsections": subsections,
    }


def build_field(
    model: Any,
    field_name: str,
    label: str,
    data_type: str | None = None,
    display_value: str | None = None,
):
    field = getattr(model, field_name)
    if data_type is None:
        if isinstance(field, datetime):
            data_type = "datetime"
        elif isinstance(field, date):
            data_type = "date"
        elif isinstance(field, str) or isinstance(field, int) or field is None:
            data_type = "str"

    if data_type == "date":
        value = field.isoformat()
        display_value = amp_date(field)
    elif data_type == "datetime":
        value = field.isoformat()
        display_value = amp_datetime(field)
    elif data_type == "link":
        value = field
    elif data_type == "str":
        value = field
        if hasattr(model, f"get_{field_name}_display"):
            display_value = getattr(model, f"get_{field_name}_display")()
    elif data_type == "markdown":
        value = field
    else:
        raise ValueError("Unknown data_type", data_type, model, field_name)

    return {
        "name": field_name,
        "data_type": data_type,
        "label": label,
        "value": value,
        "display_value": display_value,
    }
