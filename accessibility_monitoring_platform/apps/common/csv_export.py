"""Utility functions for CSV exports"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

from ..detailed.models import Contact as DetailedContact
from ..detailed.models import DetailedCase
from ..reports.models import Report
from ..simplified.models import CaseStatus
from ..simplified.models import Contact as SimplifiedContact
from ..simplified.models import SimplifiedCase

WCAG_AUDIT_INITIAL: str = "WcagAudit Initial"
WCAG_AUDIT_TWELVE_WEEK: str = "WcagAudit TwelveWeek"
STATEMENT_AUDIT_INITIAL: str = "StatementAudit Initial"
STATEMENT_AUDIT_TWELVE_WEEK: str = "StatementAudit TwelveWeek"


ExportableClassKeys = Literal[
    WCAG_AUDIT_INITIAL,
    WCAG_AUDIT_TWELVE_WEEK,
    STATEMENT_AUDIT_INITIAL,
    STATEMENT_AUDIT_TWELVE_WEEK,
    DetailedCase,
    DetailedContact,
    CaseStatus,
    Report,
    SimplifiedCase,
    SimplifiedContact,
    None,
]


@dataclass
class CSVColumn:
    """Data to use when building export CSV"""

    column_header: str
    source_classkey: ExportableClassKeys
    source_attr: str
    formatted_data: str = ""


@dataclass
class EqualityBodyCSVColumn(CSVColumn):
    """Data to use when building export CSV for equality body and to show in UI"""

    data_type: Literal["str", "url", "markdown", "pre"] = "str"
    required: bool = False
    formatted_data: str = ""
    default_data: str = ""
    ui_suffix: str = ""
    edit_url_classkey: ExportableClassKeys = None
    edit_url_name: str | None = None
    edit_url_label: str = "Edit"
    edit_url_anchor: str = ""
    edit_url: str | None = None

    @property
    def required_data_missing(self):
        return self.required and (
            self.formatted_data is None or self.formatted_data == self.default_data
        )


def format_model_field(
    source_instance: ExportableClassKeys,
    column: CSVColumn,
) -> str:
    """
    For a model field, return the value, suitably formatted.
    """
    if source_instance is None:
        return ""
    value: Any = getattr(source_instance, column.source_attr, "")
    get_display_name: str = f"get_{column.source_attr}_display"
    if isinstance(value, date) or isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    elif column.source_attr == "enforcement_body":
        return value.upper()
    elif hasattr(source_instance, get_display_name):
        return getattr(source_instance, get_display_name)()
    else:
        return value
