"""Utilities to build JSON serialisable data to store in Case.archive"""
from datetime import date, datetime

from .templatetags.common_tags import amp_date, amp_datetime


def build_section(name, complete_date, fields, subsections=None):
    complete_flag = complete_date.isoformat() if complete_date else None
    return {
        "name": name,
        "complete": complete_flag,
        "fields": fields,
        "subsections": subsections,
    }


def build_field(object, field_name, label, data_type=None, display_value=None):
    field = getattr(object, field_name)
    if data_type is None:
        if isinstance(field, datetime):
            data_type = "datetime"
        elif isinstance(field, date):
            data_type = "date"
        else:
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
        if hasattr(object, f"get_{field_name}_display"):
            display_value = getattr(object, f"get_{field_name}_display")()
    elif data_type == "markdown":
        value = field
    else:
        raise ValueError("Unknown data_type", data_type)

    return {
        "name": field_name,
        "data_type": data_type,
        "label": label,
        "value": value,
        "display_value": display_value,
    }
