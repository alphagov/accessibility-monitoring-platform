""" Utility function to build context object for view pages sections """

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Match, Optional, Tuple, Union

from django.utils.text import slugify

from .form_extract_utils import FieldLabelAndValue


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
    display_fields: List[FieldLabelAndValue] = None
    subtables: List[ViewSubTable] = None
    subsections: List["ViewSection"] = None


def build_view_section(
    name: str,
    edit_url: str,
    edit_url_id: str,
    complete_date: Optional[date] = None,
    anchor: Optional[str] = None,
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
        display_fields=display_fields,
        subtables=subtables,
        subsections=subsections,
    )
