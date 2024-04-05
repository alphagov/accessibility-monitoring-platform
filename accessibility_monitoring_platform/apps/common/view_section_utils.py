"""
Utility function to build context object for view pages' sections
"""

from dataclasses import dataclass
from datetime import date
from typing import ClassVar, List, Literal, Optional

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
    name: str
    anchor: str = ""
    edit_url: str = ""
    edit_url_id: str = ""
    complete: bool = False
    display_fields: List[FieldLabelAndValue] = None
    subtables: List[ViewSubTable] = None
    subsections: List["ViewSection"] = None
    INITIAL_WCAG_RESULTS: ClassVar[str] = "initial-wcag-results"
    INITIAL_STATEMENT_RESULTS: ClassVar[str] = "initial-statement-results"
    TWELVE_WEEK_WCAG_RESULTS: ClassVar[str] = "12-week-wcag-results"
    TWELVE_WEEK_STATEMENT_RESULTS: ClassVar[str] = "12-week-statement-results"
    FORM_TYPE: ClassVar[str] = "form"
    type: Literal[
        FORM_TYPE,
        INITIAL_WCAG_RESULTS,
        INITIAL_STATEMENT_RESULTS,
        TWELVE_WEEK_WCAG_RESULTS,
        TWELVE_WEEK_STATEMENT_RESULTS,
    ] = FORM_TYPE
    page: Optional[Page] = None
    statement_check_results: QuerySet[StatementCheckResult] = None

    def __post_init__(self):
        if (
            self.type in [self.INITIAL_WCAG_RESULTS, self.TWELVE_WEEK_WCAG_RESULTS]
            and self.page is None
        ):
            raise ValueError("Page missing from WCAG results section.")
        if (
            self.type
            in [self.INITIAL_STATEMENT_RESULTS, self.TWELVE_WEEK_STATEMENT_RESULTS]
            and self.statement_check_results is None
        ):
            raise ValueError("Results missing from statement results section.")


def build_view_section(
    name: str,
    edit_url: str = "",
    edit_url_id: str = "",
    complete_date: Optional[date] = None,
    anchor: Optional[str] = None,
    display_fields: Optional[List[FieldLabelAndValue]] = None,
    subtables: Optional[ViewSubTable] = None,
    subsections: Optional[ViewSection] = None,
    type: str = ViewSection.FORM_TYPE,
    page: Optional[Page] = None,
    statement_check_results: QuerySet[StatementCheckResult] = None,
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
        type=type,
        page=page,
        statement_check_results=statement_check_results,
    )
