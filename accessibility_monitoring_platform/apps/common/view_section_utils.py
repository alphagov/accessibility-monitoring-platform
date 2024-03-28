""" Utility function to build context object for view pages sections """

from dataclasses import dataclass
from datetime import date
from typing import Any, ClassVar, List, Optional, Type

from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify

from .form_extract_utils import EXCLUDED_FIELDS, EXTRA_LABELS, FieldLabelAndValue
from .forms import AMPTextField, AMPURLField
from .models import Sector


@dataclass
class ViewTableCell:
    header: bool = False
    markdown: bool = False
    css_class: str = "amp-font-weight-normal amp-width-one-half"
    content: str = ""
    extra_label: str = ""
    DATE_TYPE: ClassVar[str] = "date"
    NOTES_TYPE: ClassVar[str] = "notes"
    URL_TYPE: ClassVar[str] = "url"
    TEXT_TYPE: ClassVar[str] = "text"
    type: str = TEXT_TYPE


@dataclass
class ViewTableRow:
    cells: List[ViewTableCell] = None


@dataclass
class ViewTable:
    header_row: Optional[ViewTableRow] = None
    rows: List[ViewTableRow] = None


@dataclass
class ViewSubTable:
    name: str
    display_fields: List[FieldLabelAndValue] = None


@dataclass
class ViewSection:
    name: str
    anchor: str = ""
    edit_url: str = ""
    edit_url_id: str = ""
    complete: bool = False
    display_table: Optional[ViewTable] = None
    display_fields: List[FieldLabelAndValue] = None
    subtables: List[ViewSubTable] = None
    subsections: List["ViewSection"] = None


def build_table_from_form(  # noqa: C901
    instance: models.Model,
    form: Type[forms.Form],
    excluded_fields: Optional[List[str]] = None,
) -> ViewTable:
    """
    Extract field labels from form and values from case for use in html table rows
    """
    rows: List[ViewTableRow] = []
    if excluded_fields is None:
        excluded_fields = []
    for field_name, field in form.fields.items():
        if field_name in EXCLUDED_FIELDS:
            continue
        if field_name in excluded_fields:
            continue
        type_of_value: str = FieldLabelAndValue.TEXT_TYPE
        value: Any = getattr(instance, field_name)
        if isinstance(value, User):
            value = value.get_full_name()
        elif field_name == "sector" and value is None:
            value = "Unknown"
        elif isinstance(value, Sector):
            value = str(value)
        elif isinstance(field, forms.ModelChoiceField):
            pass
        elif isinstance(field, forms.ChoiceField):
            value = getattr(instance, f"get_{field_name}_display")()
        elif isinstance(field, AMPURLField):
            type_of_value = ViewTableCell.URL_TYPE
        elif isinstance(field, AMPTextField):
            type_of_value = ViewTableCell.NOTES_TYPE
        elif isinstance(value, date):
            type_of_value = ViewTableCell.DATE_TYPE
        if field.label == "Notes" and not value:
            continue
        rows.append(
            ViewTableRow(
                cells=[
                    ViewTableCell(content=field.label),
                    ViewTableCell(
                        content=value,
                        type=type_of_value,
                        extra_label=EXTRA_LABELS.get(field_name, ""),
                    ),
                ]
            )
        )
    return ViewTable(rows=rows)


def build_view_section(
    name: str,
    edit_url: str = "",
    edit_url_id: str = "",
    complete_date: Optional[date] = None,
    anchor: Optional[str] = None,
    display_table: Optional[ViewTable] = None,
    display_fields: Optional[List[FieldLabelAndValue]] = None,
    subtables: Optional[ViewSubTable] = None,
    subsections: Optional[ViewSection] = None,
) -> ViewSection:
    complete_flag = True if complete_date else False
    anchor = slugify(name) if anchor is None else anchor
    return ViewSection(
        name=name,
        anchor=anchor,
        edit_url=edit_url,
        edit_url_id=edit_url_id,
        complete=complete_flag,
        display_table=display_table,
        display_fields=display_fields,
        subtables=subtables,
        subsections=subsections,
    )
