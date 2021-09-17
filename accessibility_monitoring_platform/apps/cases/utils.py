"""
Utility functions for cases app
"""

import csv
from dataclasses import dataclass
from datetime import date
from typing import Any, ClassVar, Dict, List, Tuple, Union

from django import forms
from django.contrib.auth.models import User
from django.db.models import Q, QuerySet
from django.http import HttpResponse

from ..common.forms import AMPTextField, AMPURLField
from ..common.utils import build_filters

from .forms import (
    CaseDetailUpdateForm,
    CaseSearchForm,
    CaseTestResultsUpdateForm,
    CaseReportDetailsUpdateForm,
    CaseReportCorrespondenceUpdateForm,
    CaseFinalDecisionUpdateForm,
    DEFAULT_SORT,
)

from .models import Case, STATUS_READY_TO_QA

EXTRA_LABELS = {
    "test_results_url": "Monitor document",
    "report_draft_url": "Report draft",
    "report_final_pdf_url": "Final PDF draft",
    "report_final_odt_url": "Final ODT draft",
}

EXCLUDED_FIELDS = [
    "case_details_complete_date",
    "testing_details_complete_date",
    "reporting_details_complete_date",
    "report_correspondence_complete_date",
    "final_decision_complete_date",
    "enforcement_correspondence_complete_date",
]

CASE_FIELD_AND_FILTER_NAMES: List[Tuple[str, str]] = [
    ("auditor", "auditor_id"),
    ("reviewer", "reviewer_id"),
    ("status", "status"),
    ("start_date", "created__gte"),
    ("end_date", "created__lte"),
]

CONTACT_NAME_COLUMN_NUMBER = 3
JOB_TITLE_COLUMN_NUMBER = 4
CONTACT_DETAIL_COLUMN_NUMBER = 5
CONTACT_NOTES_COLUMN_NUMBER = 6

COLUMN_NUMBER_BY_FIELD: dict = {
    "id": 0,
    "created": 1,
    "organisation_name": 2,
    "is_complaint": 7,
    "report_final_pdf_url": 8,
    "report_sent_date": 9,
    "report_acknowledged_date": 10,
    "report_followup_week_12_due_date": 11,
    "psb_progress_notes": 12,
    "is_disproportionate_claimed": 13,
    "disproportionate_notes": 14,
    "accessibility_statement_state_final": 15,
    "accessibility_statement_notes_final": 16,
    "accessibility_statement_screenshot_url": 17,
    "is_website_compliant": 18,
    "compliance_decision_notes": 19,
    "retested_website_date": 20,
    "compliance_email_sent_date": 21,
    "psb_location": 22,
    "home_page_url": 23,
}

COLUMNS_FOR_EHRC = [
    "Case No.",
    "Date",
    "Website",
    "Contact name",
    "Job title",
    "Contact detail",
    "Contact notes",
    "Is it a complaint?",
    "Link to report",
    "Report sent on",
    "Report acknowledged",
    "Followup date - 12 week deadline",
    "Summary of progress made / response from PSB",
    "Disproportionate Burden Claimed?",
    "Disproportionate Burden Notes",
    "Accessibility Statement Decision",
    "Notes on accessibility statement",
    "Link to new saved screen shot of accessibility statement if not compliant",
    "Compliance Decision",
    "Compliance Decision Notes",
    "Retest date",
    "Decision email sent?",
    "Country",
    "Home page URL",
]


@dataclass
class CaseFieldLabelAndValue:
    """Data to use in html table row of View case page"""

    value: Union[str, date]
    label: str
    type: str = "text"
    extra_label: str = ""
    DATE_TYPE: ClassVar[str] = "date"
    NOTES_TYPE: ClassVar[str] = "notes"
    URL_TYPE: ClassVar[str] = "url"
    TEXT_TYPE: ClassVar[str] = "text"


def extract_labels_and_values(
    case: Case,
    form: Union[
        CaseDetailUpdateForm,
        CaseTestResultsUpdateForm,
        CaseReportDetailsUpdateForm,
        CaseFinalDecisionUpdateForm,
    ],
) -> List[CaseFieldLabelAndValue]:
    """Extract field labels from form and values from case for use in html rows"""
    display_rows: List[CaseFieldLabelAndValue] = []
    for field_name, field in form.fields.items():
        if field_name in EXCLUDED_FIELDS:
            continue
        type_of_value = CaseFieldLabelAndValue.TEXT_TYPE
        value = getattr(case, field_name)
        if isinstance(value, User):
            value = value.get_full_name()
        elif field_name == "sector" and value is None:
            value = "Unknown"
        elif isinstance(field, forms.ModelChoiceField):
            pass
        elif isinstance(field, forms.ChoiceField):
            value = getattr(case, f"get_{field_name}_display")()
        elif isinstance(field, AMPURLField):
            type_of_value = CaseFieldLabelAndValue.URL_TYPE
        elif isinstance(field, AMPTextField):
            type_of_value = CaseFieldLabelAndValue.NOTES_TYPE
        elif isinstance(value, date):
            type_of_value = CaseFieldLabelAndValue.DATE_TYPE
        display_rows.append(
            CaseFieldLabelAndValue(
                type=type_of_value,
                label=field.label,
                value=value,
                extra_label=EXTRA_LABELS.get(field_name, ""),
            )
        )
    return display_rows


def get_sent_date(
    form: CaseReportCorrespondenceUpdateForm, case_from_db: Case, sent_date_name: str
) -> Union[date, None]:
    """
    Work out what value to save in a sent date field on the case.
    If there is a new value in the form, don't replace an existing date on the database.
    If there is a new value in the form and no date on the database then use the date from the form.
    If there is no value in the form (i.e. the checkbox is unchecked), set the date on the database to None.
    """
    date_on_form: date = form.cleaned_data.get(sent_date_name)
    if date_on_form is None:
        return None
    date_on_db: date = getattr(case_from_db, sent_date_name)
    return date_on_db if date_on_db else date_on_form


def filter_cases(form: CaseSearchForm) -> QuerySet[Case]:
    """Return a queryset of Cases filtered by the values in CaseSearchForm"""
    filters: Dict = {}
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
        if form.cleaned_data["search"]:
            search: str = form.cleaned_data["search"]
            search_query = (
                Q(organisation_name__icontains=search)
                | Q(home_page_url__icontains=search)
                | Q(id__icontains=search)
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

    return Case.objects.filter(search_query, **filters).order_by(sort_by)


def download_ehrc_cases(
    cases: QuerySet[Case],
    filename: str = "ehrc_cases.csv",
) -> HttpResponse:
    """Given a Case queryset, download the data in csv format for EHRC"""
    response: Any = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"

    writer: Any = csv.writer(response)
    writer.writerow(COLUMNS_FOR_EHRC)

    output: List[List[str]] = []
    for case in cases:
        row = ["" for _ in COLUMNS_FOR_EHRC]
        for field_name, column_number in COLUMN_NUMBER_BY_FIELD.items():
            row[column_number] = getattr(case, field_name)

        contacts = list(case.contact_set.filter(is_deleted=False))
        contact_name = "\n".join(
            [f"{contact.first_name} {contact.last_name}" for contact in contacts]
        )
        job_title = "\n".join([contact.job_title for contact in contacts])
        contact_detail = "\n".join([contact.email for contact in contacts])
        contact_notes = "\n\n".join([contact.notes for contact in contacts])
        row[CONTACT_NAME_COLUMN_NUMBER] = contact_name
        row[JOB_TITLE_COLUMN_NUMBER] = job_title
        row[CONTACT_DETAIL_COLUMN_NUMBER] = contact_detail
        row[CONTACT_NOTES_COLUMN_NUMBER] = contact_notes
        output.append(row)

    writer.writerows(output)

    return response
