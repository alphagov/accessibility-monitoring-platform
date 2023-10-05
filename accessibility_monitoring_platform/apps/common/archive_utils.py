"""Utilities to build JSON serialisable data to store in Case.archive"""
from datetime import date, datetime


def build_section(name, complete_date, fields, subsections=None):
    complete_flag = complete_date.isoformat() if complete_date else None
    return {
        "name": name,
        "complete": complete_flag,
        "fields": fields,
        "subsections": subsections,
    }


def build_field(object, field_name, label, type=None, value_display=None):
    field = getattr(object, field_name)
    if type is None:
        if isinstance(field, datetime):
            type = "datetime"
        elif isinstance(field, date):
            type = "date"
        else:
            type = "str"

    if type == "date":
        value = field.isoformat()
        value_display = f"{field:%-d %B %Y}"
    elif type == "datetime":
        value = field.isoformat()
        value_display = f"{field:%-d %B %Y %-I:%M%p}"
    elif type == "link":
        value = field
    elif type == "str":
        value = field
        if hasattr(object, f"get_{field_name}_display"):
            value_display = getattr(object, f"get_{field_name}_display")()
    elif type == "markdown":
        value = field
    else:
        raise ValueError("Unknown type", type)

    return {
        "name": field_name,
        "type": type,
        "label": label,
        "value": value,
        "value_display": value_display,
    }
