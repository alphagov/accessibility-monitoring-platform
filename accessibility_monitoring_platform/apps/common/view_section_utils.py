"""
Utility function to build context object for view pages' sections
"""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import List, Optional

from django.db.models.query import QuerySet
from django.utils.text import slugify

from ..audits.models import Page, StatementCheckResult
from .form_extract_utils import FieldLabelAndValue


@dataclass
class ViewSubTable:
    name: str
    display_fields: List[FieldLabelAndValue] = None


@dataclass
class ViewSection:
    class Type(StrEnum):
        AUDIT_RESULTS_ON_VIEW_CASE: str = "audit-results-on-view-case"
        INITIAL_WCAG_RESULTS: str = "initial-wcag-results"
        INITIAL_STATEMENT_RESULTS: str = "initial-statement-results"
        TWELVE_WEEK_WCAG_RESULTS: str = "12-week-wcag-results"
        TWELVE_WEEK_STATEMENT_RESULTS: str = "12-week-statement-results"
        FORM_TYPE: str = "form"

    name: str
    anchor: str = ""
    edit_url: str = ""
    edit_url_id: str = ""
    complete: bool = False
    display_fields: List[FieldLabelAndValue] = None
    subtables: List[ViewSubTable] = None
    subsections: List["ViewSection"] = None
    placeholder: str = "None"
    type: Type = Type.FORM_TYPE
    page: Optional[Page] = None
    statement_check_results: QuerySet[StatementCheckResult] = None

    @property
    def has_content(self) -> bool:
        return (
            (self.display_fields is not None and self.display_fields != [])
            or (self.subtables is not None and self.subtables != [])
            or (self.subsections is not None and self.subsections != [])
            or self.page is not None
            or self.statement_check_results is not None
        )

    def __post_init__(self):
        if (
            self.type
            in [
                ViewSection.Type.INITIAL_WCAG_RESULTS,
                ViewSection.Type.TWELVE_WEEK_WCAG_RESULTS,
            ]
            and self.page is None
        ):
            raise ValueError("Page missing from WCAG results section.")
        if (
            self.type
            in [
                ViewSection.Type.INITIAL_STATEMENT_RESULTS,
                ViewSection.Type.TWELVE_WEEK_STATEMENT_RESULTS,
            ]
            and self.statement_check_results is None
        ):
            raise ValueError("Results missing from statement results section.")


def build_view_section(
    name: str,
    edit_url: str = "",
    edit_url_id: str = "",
    complete_date: Optional[date] = None,
    anchor: Optional[str] = None,
    placeholder: str = "None",
    display_fields: Optional[List[FieldLabelAndValue]] = None,
    subtables: Optional[ViewSubTable] = None,
    subsections: Optional[ViewSection] = None,
    type: str = ViewSection.Type.FORM_TYPE,
    page: Optional[Page] = None,
    statement_check_results: QuerySet[StatementCheckResult] = None,
) -> ViewSection:
    complete_flag = True if complete_date else False
    anchor = slugify(name) if anchor is None else anchor
    return ViewSection(
        name=name,
        edit_url=edit_url,
        edit_url_id=edit_url_id,
        complete=complete_flag,
        anchor=anchor,
        placeholder=placeholder,
        display_fields=display_fields,
        subtables=subtables,
        subsections=subsections,
        type=type,
        page=page,
        statement_check_results=statement_check_results,
    )
