"""
Utility functions for cases app
"""

from collections import namedtuple
import csv
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from django import forms
from django.db.models import Q, QuerySet
from django.http import HttpResponse

from ..audits.models import Audit
from ..common.utils import build_filters

from .forms import CaseSearchForm, DEFAULT_SORT

from .models import Case, Contact, STATUS_READY_TO_QA

CASE_FIELD_AND_FILTER_NAMES: List[Tuple[str, str]] = [
    ("auditor", "auditor_id"),
    ("reviewer", "reviewer_id"),
    ("status", "status"),
    ("date_start", "sent_to_enforcement_body_sent_date__gte"),
    ("date_end", "sent_to_enforcement_body_sent_date__lte"),
    ("sector", "sector_id"),
]

CONTACT_NAME_COLUMN_NAME = "Contact name"
JOB_TITLE_COLUMN_NAME = "Job title"
CONTACT_DETAIL_COLUMN_NAME = "Contact detail"
CONTACT_NOTES_COLUMN_NUMBER = "Contact notes"

ColumnAndFieldNames = namedtuple("ColumnAndFieldNames", ["column_name", "field_name"])

COLUMNS_FOR_EHRC = [
    ColumnAndFieldNames(
        column_name="Equality body",
        field_name="enforcement_body",
    ),
    ColumnAndFieldNames(column_name="Test type", field_name="test_type"),
    ColumnAndFieldNames(column_name="Case No.", field_name="id"),
    ColumnAndFieldNames(column_name="Case completed date", field_name="completed_date"),
    ColumnAndFieldNames(column_name="Organisation", field_name="organisation_name"),
    ColumnAndFieldNames(column_name="Website URL", field_name="home_page_url"),
    ColumnAndFieldNames(column_name="Is it a complaint?", field_name="is_complaint"),
    ColumnAndFieldNames(
        column_name="Link to report", field_name="report_final_pdf_url"
    ),
    ColumnAndFieldNames(
        column_name="Enforcement recommendation",
        field_name="recommendation_for_enforcement",
    ),
    ColumnAndFieldNames(
        column_name="Enforcement recommendation notes",
        field_name="recommendation_notes",
    ),
    ColumnAndFieldNames(
        column_name="Summary of progress made / response from PSB",
        field_name="psb_progress_notes",
    ),
    ColumnAndFieldNames(
        column_name="Disproportionate Burden Claimed?",
        field_name="is_disproportionate_claimed",
    ),
    ColumnAndFieldNames(
        column_name="Disproportionate Burden Notes", field_name="disproportionate_notes"
    ),
    ColumnAndFieldNames(
        column_name="Accessibility Statement Decision",
        field_name="accessibility_statement_state_final",
    ),
    ColumnAndFieldNames(
        column_name="Notes on accessibility statement",
        field_name="accessibility_statement_notes_final",
    ),
    ColumnAndFieldNames(column_name=CONTACT_DETAIL_COLUMN_NAME, field_name=None),
    ColumnAndFieldNames(column_name=CONTACT_NAME_COLUMN_NAME, field_name=None),
    ColumnAndFieldNames(column_name=JOB_TITLE_COLUMN_NAME, field_name=None),
    ColumnAndFieldNames(column_name="Report sent on", field_name="report_sent_date"),
    ColumnAndFieldNames(
        column_name="Report acknowledged", field_name="report_acknowledged_date"
    ),
    ColumnAndFieldNames(
        column_name="Followup date - 12-week deadline",
        field_name="report_followup_week_12_due_date",
    ),
    ColumnAndFieldNames(column_name="Retest date", field_name="retested_website_date"),
]

CAPITALISE_FIELDS = [
    "test_type",
    "is_complaint",
    "is_disproportionate_claimed",
    "accessibility_statement_state_final",
    "recommendation_for_enforcement",
    "audit_retest_disproportionate_burden_state",
]


def get_sent_date(
    form: forms.ModelForm, case_from_db: Case, sent_date_name: str
) -> Union[date, None]:
    """
    Work out what value to save in a sent date field on the case.
    If there is a new value in the form, don't replace an existing date on the database.
    If there is a new value in the form and no date on the database then use the date from the form.
    If there is no value in the form (i.e. the checkbox is unchecked), set the date on the database to None.
    """
    date_on_form: Optional[date] = form.cleaned_data.get(sent_date_name)
    if date_on_form is None:
        return None
    date_on_db: date = getattr(case_from_db, sent_date_name)
    return date_on_db if date_on_db else date_on_form


def filter_cases(form: CaseSearchForm) -> QuerySet[Case]:
    """Return a queryset of Cases filtered by the values in CaseSearchForm"""
    filters: Dict = {}  # type: ignore
    search_query = Q()
    sort_by: str = DEFAULT_SORT

    if hasattr(form, "cleaned_data"):
        filters: Dict[str, Any] = build_filters(
            cleaned_data=form.cleaned_data,
            field_and_filter_names=CASE_FIELD_AND_FILTER_NAMES,
        )
        sort_by: str = form.cleaned_data.get("sort_by", DEFAULT_SORT)
        if not sort_by:
            sort_by: str = DEFAULT_SORT
        if form.cleaned_data["case_search"]:
            search: str = form.cleaned_data["case_search"]
            if (
                search.isdigit()
            ):  # if its just a number, it presumes its an ID and returns that case
                search_query = Q(id=search)
            else:
                search_query = (
                    Q(  # pylint: disable=unsupported-binary-operation
                        organisation_name__icontains=search
                    )
                    | Q(home_page_url__icontains=search)
                    | Q(psb_location__icontains=search)
                    | Q(sector__name__icontains=search)
                )

    if filters.get("status", "") != "deleted":
        filters["is_deleted"] = False

    if filters.get("status", "") == STATUS_READY_TO_QA:
        filters["qa_status"] = STATUS_READY_TO_QA
        del filters["status"]

    if "auditor_id" in filters and filters["auditor_id"] == "none":
        filters["auditor_id"] = None
    if "reviewer_id" in filters and filters["reviewer_id"] == "none":
        filters["reviewer_id"] = None

    return (
        Case.objects.filter(search_query, **filters)
        .order_by(sort_by)
        .select_related("auditor", "reviewer")
        .all()
    )


def format_contacts(contacts: List[Contact], column: ColumnAndFieldNames) -> str:
    """
    For a contact-related field, concatenate the values for all the contacts
    and return as a single string.
    """
    if column.column_name == CONTACT_NAME_COLUMN_NAME:
        return "\n".join([contact.name for contact in contacts])
    elif column.column_name == JOB_TITLE_COLUMN_NAME:
        return "\n".join([contact.job_title for contact in contacts])
    elif column.column_name == CONTACT_DETAIL_COLUMN_NAME:
        return "\n".join([contact.email for contact in contacts])
    elif column.column_name == CONTACT_NOTES_COLUMN_NUMBER:
        return "\n\n".join([contact.notes for contact in contacts])
    return ""


def format_model_field(
    model_instance: Union[Audit, Case], column: ColumnAndFieldNames
) -> str:
    """
    For a model field, return the value, suitably formatted.
    """
    value: Any = getattr(model_instance, column.field_name, "")
    if isinstance(value, date) or isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    elif column.field_name == "enforcement_body":
        return value.upper()
    elif column.field_name in CAPITALISE_FIELDS:
        return value.capitalize().replace("-", " ")
    else:
        return value


def download_ehrc_cases(
    cases: QuerySet[Case],
    filename: str = "ehrc_cases.csv",
) -> HttpResponse:
    """Given a Case queryset, download the data in csv format for EHRC and ECNI"""
    response: Any = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"

    writer: Any = csv.writer(response)
    writer.writerow(
        [
            column.column_name
            for column in COLUMNS_FOR_EHRC
        ]
    )

    output: List[List[str]] = []
    for case in cases:
        contacts: List[Contact] = list(case.contact_set.filter(is_deleted=False))  # type: ignore
        row = []
        for column in COLUMNS_FOR_EHRC:
            if column.field_name is None:
                row.append(format_contacts(contacts=contacts, column=column))
            else:
                row.append(format_model_field(model_instance=case, column=column))
        output.append(row)
    writer.writerows(output)

    return response
