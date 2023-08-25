"""
Utility functions for cases app
"""

from collections import namedtuple
import copy
import csv
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from django import forms
from django.contrib.auth.models import User
from django.db.models import Q, QuerySet, Case as DjangoCase, When

from django.http import HttpResponse
from django.http.request import QueryDict
from django.urls import reverse

from ..audits.models import Audit
from ..common.utils import build_filters

from .forms import CaseSearchForm, DEFAULT_SORT, NO_FILTER

from .models import (
    Case,
    CaseEvent,
    Contact,
    STATUS_UNASSIGNED,
    STATUS_READY_TO_QA,
    CASE_EVENT_TYPE_CREATE,
    CASE_EVENT_AUDITOR,
    CASE_EVENT_CREATE_AUDIT,
    CASE_EVENT_READY_FOR_QA,
    CASE_EVENT_QA_AUDITOR,
    CASE_EVENT_APPROVE_REPORT,
    CASE_EVENT_READY_FOR_FINAL_DECISION,
    CASE_EVENT_CASE_COMPLETED,
)

CASE_FIELD_AND_FILTER_NAMES: List[Tuple[str, str]] = [
    ("auditor", "auditor_id"),
    ("reviewer", "reviewer_id"),
    ("status", "status"),
    ("sector", "sector_id"),
]

CONTACT_NAME_COLUMN_NAME = "Contact name"
JOB_TITLE_COLUMN_NAME = "Job title"
CONTACT_DETAIL_COLUMN_NAME = "Contact detail"
CONTACT_NOTES_COLUMN_NUMBER = "Contact notes"

ColumnAndFieldNames = namedtuple("ColumnAndFieldNames", ["column_name", "field_name"])

COLUMNS_FOR_EQUALITY_BODY: List[ColumnAndFieldNames] = [
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
        column_name="Enforcement recommendation notes including exemptions",
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
    ColumnAndFieldNames(
        column_name="Published report", field_name="published_report_url"
    ),
    ColumnAndFieldNames(
        column_name="Previous Case No.", field_name="previous_case_number"
    ),
    ColumnAndFieldNames(
        column_name="No response to report",
        field_name="no_psb_contact",
    ),
    ColumnAndFieldNames(
        column_name="% of issues fixed",
        field_name="percentage_website_issues_fixed",
    ),
]

EXTRA_AUDIT_COLUMNS_FOR_EQUALITY_BODY: List[ColumnAndFieldNames] = [
    ColumnAndFieldNames(
        column_name="Initial disproportionate burden claimed?",
        field_name="disproportionate_burden_state",
    ),
    ColumnAndFieldNames(
        column_name="Initial disproportionate notes",
        field_name="disproportionate_burden_notes",
    ),
    ColumnAndFieldNames(
        column_name="Final disproportionate burden claimed?",
        field_name="audit_retest_disproportionate_burden_state",
    ),
    ColumnAndFieldNames(
        column_name="Final disproportionate notes",
        field_name="audit_retest_disproportionate_burden_notes",
    ),
]

CASE_COLUMNS_FOR_EXPORT: List[ColumnAndFieldNames] = [
    ColumnAndFieldNames(column_name="Case no.", field_name="id"),
    ColumnAndFieldNames(column_name="Version", field_name="version"),
    ColumnAndFieldNames(column_name="Created by", field_name="created_by"),
    ColumnAndFieldNames(column_name="Date created", field_name="created"),
    ColumnAndFieldNames(column_name="Status", field_name="status"),
    ColumnAndFieldNames(column_name="Auditor", field_name="auditor"),
    ColumnAndFieldNames(column_name="Type of test", field_name="test_type"),
    ColumnAndFieldNames(column_name="Full URL", field_name="home_page_url"),
    ColumnAndFieldNames(column_name="Domain name", field_name="domain"),
    ColumnAndFieldNames(
        column_name="Organisation name", field_name="organisation_name"
    ),
    ColumnAndFieldNames(
        column_name="Public sector body location", field_name="psb_location"
    ),
    ColumnAndFieldNames(column_name="Sector", field_name="sector"),
    ColumnAndFieldNames(
        column_name="Which equalities body will check the case?",
        field_name="enforcement_body",
    ),
    ColumnAndFieldNames(
        column_name="Testing methodology", field_name="testing_methodology"
    ),
    ColumnAndFieldNames(
        column_name="Report methodology", field_name="report_methodology"
    ),
    ColumnAndFieldNames(column_name="Complaint?", field_name="is_complaint"),
    ColumnAndFieldNames(
        column_name="URL to previous case", field_name="previous_case_url"
    ),
    ColumnAndFieldNames(column_name="Trello ticket URL", field_name="trello_url"),
    ColumnAndFieldNames(column_name="Case details notes", field_name="notes"),
    ColumnAndFieldNames(
        column_name="Case details page complete",
        field_name="case_details_complete_date",
    ),
    ColumnAndFieldNames(
        column_name="Link to test results spreadsheet", field_name="test_results_url"
    ),
    ColumnAndFieldNames(
        column_name="Spreadsheet test status", field_name="test_status"
    ),
    ColumnAndFieldNames(
        column_name="Initial accessibility statement compliance decision",
        field_name="accessibility_statement_state",
    ),
    ColumnAndFieldNames(
        column_name="Initial accessibility statement compliance notes",
        field_name="accessibility_statement_notes",
    ),
    ColumnAndFieldNames(
        column_name="Initial website compliance decision",
        field_name="website_compliance_state_initial",
    ),
    ColumnAndFieldNames(
        column_name="Initial website compliance notes",
        field_name="compliance_decision_notes",
    ),
    ColumnAndFieldNames(
        column_name="Testing details page complete",
        field_name="testing_details_complete_date",
    ),
    ColumnAndFieldNames(
        column_name="Link to report draft", field_name="report_draft_url"
    ),
    ColumnAndFieldNames(column_name="Report details notes", field_name="report_notes"),
    ColumnAndFieldNames(
        column_name="Report details page complete",
        field_name="reporting_details_complete_date",
    ),
    ColumnAndFieldNames(
        column_name="Report ready to be reviewed?", field_name="report_review_status"
    ),
    ColumnAndFieldNames(column_name="QA auditor", field_name="reviewer"),
    ColumnAndFieldNames(
        column_name="Report approved?", field_name="report_approved_status"
    ),
    ColumnAndFieldNames(
        column_name="Link to final PDF report", field_name="report_final_pdf_url"
    ),
    ColumnAndFieldNames(
        column_name="Link to final ODT report", field_name="report_final_odt_url"
    ),
    ColumnAndFieldNames(
        column_name="QA process page complete", field_name="qa_process_complete_date"
    ),
    ColumnAndFieldNames(
        column_name="Contact details page complete",
        field_name="contact_details_complete_date",
    ),
    ColumnAndFieldNames(
        column_name="Seven day 'no contact details' email sent",
        field_name="seven_day_no_contact_email_sent_date",
    ),
    ColumnAndFieldNames(column_name="Report sent on", field_name="report_sent_date"),
    ColumnAndFieldNames(
        column_name="1-week followup sent date",
        field_name="report_followup_week_1_sent_date",
    ),
    ColumnAndFieldNames(
        column_name="4-week followup sent date",
        field_name="report_followup_week_4_sent_date",
    ),
    ColumnAndFieldNames(
        column_name="Report acknowledged", field_name="report_acknowledged_date"
    ),
    ColumnAndFieldNames(column_name="Zendesk ticket URL", field_name="zendesk_url"),
    ColumnAndFieldNames(
        column_name="Report correspondence notes", field_name="correspondence_notes"
    ),
    ColumnAndFieldNames(
        column_name="Report correspondence page complete",
        field_name="report_correspondence_complete_date",
    ),
    ColumnAndFieldNames(
        column_name="1-week followup due date",
        field_name="report_followup_week_1_due_date",
    ),
    ColumnAndFieldNames(
        column_name="4-week followup due date",
        field_name="report_followup_week_4_due_date",
    ),
    ColumnAndFieldNames(
        column_name="12-week followup due date",
        field_name="report_followup_week_12_due_date",
    ),
    ColumnAndFieldNames(
        column_name="Do you want to mark the PSB as unresponsive to this case?",
        field_name="no_psb_contact",
    ),
    ColumnAndFieldNames(
        column_name="12-week update requested",
        field_name="twelve_week_update_requested_date",
    ),
    ColumnAndFieldNames(
        column_name="12-week chaser 1-week followup sent date",
        field_name="twelve_week_1_week_chaser_sent_date",
    ),
    ColumnAndFieldNames(
        column_name="12-week update received",
        field_name="twelve_week_correspondence_acknowledged_date",
    ),
    ColumnAndFieldNames(
        column_name="12-week correspondence notes",
        field_name="twelve_week_correspondence_notes",
    ),
    ColumnAndFieldNames(
        column_name="Mark the case as having no response to 12 week deadline",
        field_name="twelve_week_response_state",
    ),
    ColumnAndFieldNames(
        column_name="12-week correspondence page complete",
        field_name="twelve_week_correspondence_complete_date",
    ),
    ColumnAndFieldNames(
        column_name="12-week chaser 1-week followup due date",
        field_name="twelve_week_1_week_chaser_due_date",
    ),
    ColumnAndFieldNames(
        column_name="12-week retest page complete",
        field_name="twelve_week_retest_complete_date",
    ),
    ColumnAndFieldNames(
        column_name="Summary of progress made from public sector body",
        field_name="psb_progress_notes",
    ),
    ColumnAndFieldNames(
        column_name="Retested website?", field_name="retested_website_date"
    ),
    ColumnAndFieldNames(
        column_name="Is this case ready for final decision?",
        field_name="is_ready_for_final_decision",
    ),
    ColumnAndFieldNames(
        column_name="Reviewing changes page complete",
        field_name="review_changes_complete_date",
    ),
    ColumnAndFieldNames(
        column_name="12-week website compliance decision",
        field_name="website_state_final",
    ),
    ColumnAndFieldNames(
        column_name="12-week website compliance decision notes",
        field_name="website_state_notes_final",
    ),
    ColumnAndFieldNames(
        column_name="Final website compliance decision page complete (spreadsheet testing)",
        field_name="final_website_complete_date",
    ),
    ColumnAndFieldNames(
        column_name="Disproportionate burden claimed? (spreadsheet testing)",
        field_name="is_disproportionate_claimed",
    ),
    ColumnAndFieldNames(
        column_name="Disproportionate burden notes (spreadsheet testing)",
        field_name="disproportionate_notes",
    ),
    ColumnAndFieldNames(
        column_name="Link to accessibility statement screenshot (spreadsheet testing)",
        field_name="accessibility_statement_screenshot_url",
    ),
    ColumnAndFieldNames(
        column_name="12-week accessibility statement compliance decision",
        field_name="accessibility_statement_state_final",
    ),
    ColumnAndFieldNames(
        column_name="12-week accessibility statement compliance notes",
        field_name="accessibility_statement_notes_final",
    ),
    ColumnAndFieldNames(
        column_name="Final accessibility statement compliance decision page complete (spreadsheet testing)",
        field_name="final_statement_complete_date",
    ),
    ColumnAndFieldNames(
        column_name="Recommendation for equality body",
        field_name="recommendation_for_enforcement",
    ),
    ColumnAndFieldNames(
        column_name="Enforcement recommendation notes including exemptions",
        field_name="recommendation_notes",
    ),
    ColumnAndFieldNames(
        column_name="Date when compliance decision email sent to public sector body",
        field_name="compliance_email_sent_date",
    ),
    ColumnAndFieldNames(column_name="Case completed", field_name="case_completed"),
    ColumnAndFieldNames(
        column_name="Date case completed first updated", field_name="completed_date"
    ),
    ColumnAndFieldNames(
        column_name="Closing the case page complete",
        field_name="case_close_complete_date",
    ),
    ColumnAndFieldNames(
        column_name="Public sector body statement appeal notes",
        field_name="psb_appeal_notes",
    ),
    ColumnAndFieldNames(
        column_name="Summary of events after the case was closed",
        field_name="post_case_notes",
    ),
    ColumnAndFieldNames(
        column_name="Post case summary page complete",
        field_name="post_case_complete_date",
    ),
    ColumnAndFieldNames(
        column_name="Case updated (on post case summary page)",
        field_name="case_updated_date",
    ),
    ColumnAndFieldNames(
        column_name="Date sent to equality body",
        field_name="sent_to_enforcement_body_sent_date",
    ),
    ColumnAndFieldNames(
        column_name="Equality body pursuing this case?",
        field_name="enforcement_body_pursuing",
    ),
    ColumnAndFieldNames(
        column_name="Equality body correspondence notes",
        field_name="enforcement_body_correspondence_notes",
    ),
    ColumnAndFieldNames(
        column_name="Equality body summary page complete",
        field_name="enforcement_correspondence_complete_date",
    ),
    ColumnAndFieldNames(column_name="Deactivated case", field_name="is_deactivated"),
    ColumnAndFieldNames(column_name="Date deactivated", field_name="deactivate_date"),
    ColumnAndFieldNames(
        column_name="Reason why (deactivated)", field_name="deactivate_notes"
    ),
    ColumnAndFieldNames(column_name="QA status", field_name="qa_status"),
    ColumnAndFieldNames(column_name="Contact detail notes", field_name="contact_notes"),
    ColumnAndFieldNames(
        column_name="Date equality body completed the case",
        field_name="enforcement_body_finished_date",
    ),
    ColumnAndFieldNames(
        column_name="% of issues fixed",
        field_name="percentage_website_issues_fixed",
    ),
]
CONTACT_COLUMNS_FOR_EXPORT: List[ColumnAndFieldNames] = [
    ColumnAndFieldNames(column_name="Contact email", field_name="email"),
]
FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT: List[ColumnAndFieldNames] = [
    ColumnAndFieldNames(column_name="Case no.", field_name="id"),
    ColumnAndFieldNames(
        column_name="Organisation name", field_name="organisation_name"
    ),
    ColumnAndFieldNames(
        column_name="Closing the case date", field_name="compliance_email_sent_date"
    ),
    ColumnAndFieldNames(
        column_name="Enforcement recommendation notes including exemptions",
        field_name="recommendation_notes",
    ),
    ColumnAndFieldNames(column_name="Contact notes", field_name="contact_notes"),
    ColumnAndFieldNames(
        column_name="Feedback survey sent?", field_name="is_feedback_requested"
    ),
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


def filter_cases(form: CaseSearchForm) -> QuerySet[Case]:  # noqa: C901
    """Return a queryset of Cases filtered by the values in CaseSearchForm"""
    filters: Dict = {}
    search_query = Q()
    sort_by: str = DEFAULT_SORT

    if hasattr(form, "cleaned_data"):
        field_and_filter_names: List[Tuple[str, str]] = copy.copy(
            CASE_FIELD_AND_FILTER_NAMES
        )
        if "date_type" in form.cleaned_data:
            date_range_field: str = form.cleaned_data["date_type"]
            field_and_filter_names.append(("date_start", f"{date_range_field}__gte"))
            field_and_filter_names.append(("date_end", f"{date_range_field}__lte"))
        filters: Dict[str, Any] = build_filters(
            cleaned_data=form.cleaned_data,
            field_and_filter_names=field_and_filter_names,
        )
        sort_by: str = form.cleaned_data.get("sort_by", DEFAULT_SORT)
        if form.cleaned_data.get("case_search"):
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
        for filter_name in ["is_complaint", "enforcement_body"]:
            filter_value: str = form.cleaned_data.get(filter_name, NO_FILTER)
            if filter_value != NO_FILTER:
                filters[filter_name] = filter_value

    if filters.get("status", "") == STATUS_READY_TO_QA:
        filters["qa_status"] = STATUS_READY_TO_QA
        del filters["status"]

    if "auditor_id" in filters and filters["auditor_id"] == "none":
        filters["auditor_id"] = None
    if "reviewer_id" in filters and filters["reviewer_id"] == "none":
        filters["reviewer_id"] = None

    if not sort_by:
        return (
            Case.objects.filter(search_query, **filters)
            .annotate(
                position_unassigned_first=DjangoCase(
                    When(status=STATUS_UNASSIGNED, then=0), default=1
                )
            )
            .order_by("position_unassigned_first", "-id")
            .select_related("auditor", "reviewer")
        )
    return (
        Case.objects.filter(search_query, **filters)
        .order_by(sort_by)
        .select_related("auditor", "reviewer")
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
    model_instance: Union[Audit, Case, Contact, None], column: ColumnAndFieldNames
) -> str:
    """
    For a model field, return the value, suitably formatted.
    """
    if model_instance is None:
        return ""
    value: Any = getattr(model_instance, column.field_name, "")
    get_display_name: str = f"get_{column.field_name}_display"
    if isinstance(value, date) or isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    elif column.field_name == "enforcement_body":
        return value.upper()
    elif hasattr(model_instance, get_display_name):
        return getattr(model_instance, get_display_name)()
    else:
        return value


def download_feedback_survey_cases(
    cases: QuerySet[Case], filename: str = "feedback_survey_cases.csv"
) -> HttpResponse:
    """Given a Case queryset, download the feedback survey data in csv format"""
    response: Any = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"

    writer: Any = csv.writer(response)
    writer.writerow(
        [
            column.column_name
            for column in FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT
            + CONTACT_COLUMNS_FOR_EXPORT
        ]
    )

    output: List[List[str]] = []
    for case in cases:
        contact: Optional[Contact] = case.contact_set.filter(is_deleted=False).first()
        row = []
        for column in FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT:
            row.append(format_model_field(model_instance=case, column=column))
        for column in CONTACT_COLUMNS_FOR_EXPORT:
            row.append(format_model_field(model_instance=contact, column=column))
        output.append(row)
    writer.writerows(output)

    return response


def download_equality_body_cases(
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
            for column in COLUMNS_FOR_EQUALITY_BODY
            + EXTRA_AUDIT_COLUMNS_FOR_EQUALITY_BODY
        ]
    )

    output: List[List[str]] = []
    for case in cases:
        contacts: List[Contact] = list(case.contact_set.filter(is_deleted=False))
        row = []
        for column in COLUMNS_FOR_EQUALITY_BODY:
            if column.field_name is None:
                row.append(format_contacts(contacts=contacts, column=column))
            else:
                row.append(format_model_field(model_instance=case, column=column))
        for column in EXTRA_AUDIT_COLUMNS_FOR_EQUALITY_BODY:
            row.append(format_model_field(model_instance=case.audit, column=column))
        output.append(row)
    writer.writerows(output)

    return response


def download_cases(cases: QuerySet[Case], filename: str = "cases.csv") -> HttpResponse:
    """Given a Case queryset, download the data in csv format"""
    response: Any = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"

    writer: Any = csv.writer(response)
    writer.writerow(
        [
            column.column_name
            for column in CASE_COLUMNS_FOR_EXPORT + CONTACT_COLUMNS_FOR_EXPORT
        ]
    )

    output: List[List[str]] = []
    for case in cases:
        contact: Optional[Contact] = case.contact_set.filter(is_deleted=False).first()
        row = []
        for column in CASE_COLUMNS_FOR_EXPORT:
            row.append(format_model_field(model_instance=case, column=column))
        for column in CONTACT_COLUMNS_FOR_EXPORT:
            row.append(format_model_field(model_instance=contact, column=column))
        output.append(row)
    writer.writerows(output)

    return response


def replace_search_key_with_case_search(request_get: QueryDict) -> Dict[str, str]:
    """Convert QueryDict to dictionary and replace key 'search' with 'case_search'."""
    search_args: Dict[str, str] = {key: value for key, value in request_get.items()}
    if "search" in search_args:
        search_args["case_search"] = search_args.pop("search")
    return search_args


def record_case_event(
    user: User, new_case: Case, old_case: Optional[Case] = None
) -> None:
    """Create a case event based on the changes between the old and new cases"""
    if old_case is None:
        CaseEvent.objects.create(
            case=new_case, done_by=user, event_type=CASE_EVENT_TYPE_CREATE
        )
        return
    if old_case.auditor != new_case.auditor:
        old_user_name: str = (
            old_case.auditor.get_full_name() if old_case.auditor is not None else "none"
        )
        new_user_name: str = (
            new_case.auditor.get_full_name() if new_case.auditor is not None else "none"
        )
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CASE_EVENT_AUDITOR,
            message=f"Auditor changed from {old_user_name} to {new_user_name}",
        )
    if old_case.audit is None and new_case.audit is not None:
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CASE_EVENT_CREATE_AUDIT,
            message="Start of test",
        )
    if old_case.report_review_status != new_case.report_review_status:
        old_status: str = old_case.get_report_review_status_display()
        new_status: str = new_case.get_report_review_status_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CASE_EVENT_READY_FOR_QA,
            message=f"Report ready to be reviewed changed from '{old_status}' to '{new_status}'",
        )
    if old_case.reviewer != new_case.reviewer:
        old_user_name: str = (
            old_case.reviewer.get_full_name()
            if old_case.reviewer is not None
            else "none"
        )
        new_user_name: str = (
            new_case.reviewer.get_full_name()
            if new_case.reviewer is not None
            else "none"
        )
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CASE_EVENT_QA_AUDITOR,
            message=f"QA auditor changed from {old_user_name} to {new_user_name}",
        )
    if old_case.report_approved_status != new_case.report_approved_status:
        old_status: str = old_case.get_report_approved_status_display()
        new_status: str = new_case.get_report_approved_status_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CASE_EVENT_APPROVE_REPORT,
            message=f"Report approved changed from '{old_status}' to '{new_status}'",
        )
    if old_case.is_ready_for_final_decision != new_case.is_ready_for_final_decision:
        old_status: str = old_case.get_is_ready_for_final_decision_display()
        new_status: str = new_case.get_is_ready_for_final_decision_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CASE_EVENT_READY_FOR_FINAL_DECISION,
            message=f"Case ready for final decision changed from '{old_status}' to '{new_status}'",
        )
    if old_case.case_completed != new_case.case_completed:
        old_status: str = old_case.get_case_completed_display()
        new_status: str = new_case.get_case_completed_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CASE_EVENT_CASE_COMPLETED,
            message=f"Case completed changed from '{old_status}' to '{new_status}'",
        )


def build_edit_link_html(case: Case, url_name: str) -> str:
    """Return html of edit link for case"""
    case_pk: Dict[str, int] = {"pk": case.id}
    edit_url: str = reverse(url_name, kwargs=case_pk)
    return (
        f"<a href='{edit_url}' class='govuk-link govuk-link--no-visited-state'>Edit</a>"
    )
