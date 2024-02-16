"""
Utility functions for cases app
"""

import copy
import csv
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from django import forms
from django.contrib.auth.models import User
from django.db.models import Case as DjangoCase
from django.db.models import Q, QuerySet, When
from django.http import HttpResponse
from django.http.request import QueryDict
from django.urls import reverse

from ..audits.models import Audit, Retest
from ..common.utils import build_filters
from ..reports.models import Report
from .forms import CaseSearchForm, Complaint, Sort
from .models import (
    COMPLIANCE_FIELDS,
    Case,
    CaseCompliance,
    CaseEvent,
    CaseStatus,
    Contact,
    EqualityBodyCorrespondence,
)

CASE_FIELD_AND_FILTER_NAMES: List[Tuple[str, str]] = [
    ("auditor", "auditor_id"),
    ("reviewer", "reviewer_id"),
    ("status", "status"),
    ("sector", "sector_id"),
    ("subcategory", "subcategory_id"),
]


@dataclass
class PostCaseAlert:
    """Data to use in html table row of post case alerts page"""

    date: date
    case: Case
    description: str
    absolute_url: str
    absolute_url_label: str


@dataclass
class CSVColumn:
    """Data to use when building export CSV"""

    column_header: str
    source_class: Union[Audit, Case, CaseCompliance]
    source_attr: str


@dataclass
class EqualityBodyCSVColumn(CSVColumn):
    """Data to use when building export CSV for equality body and to show in UI"""

    data_type: Literal["str", "url", "markdown"] = "str"
    required: bool = False
    formatted_data: str = ""
    default_data: str = ""
    edit_url_class: Union[Audit, Case, CaseCompliance, Report] = None
    edit_url_name: Optional[str] = None
    edit_url_label: str = "Edit"
    edit_url: Optional[str] = None


CONTACT_DETAILS_COLUMN_HEADER: str = "Contact details"
ORGANISATION_RESPONDED_COLUMN_HEADER: str = "Organisation responded to report?"

EQUALITY_BODY_COLUMNS_FOR_EXPORT: List[EqualityBodyCSVColumn] = [
    EqualityBodyCSVColumn(
        column_header="Equality body",
        source_class=Case,
        source_attr="enforcement_body",
        required=True,
        edit_url_class=Case,
        edit_url_name="cases:edit-case-details",
    ),
    EqualityBodyCSVColumn(
        column_header="Test type",
        source_class=Case,
        source_attr="test_type",
        required=True,
        edit_url_class=Case,
        edit_url_name=None,
    ),
    EqualityBodyCSVColumn(
        column_header="Case number",
        source_class=Case,
        source_attr="id",
        required=True,
        edit_url_class=Case,
        edit_url_name=None,
    ),
    EqualityBodyCSVColumn(
        column_header="Organisation",
        source_class=Case,
        source_attr="organisation_name",
        required=True,
        edit_url_class=Case,
        edit_url_name="cases:edit-case-details",
    ),
    EqualityBodyCSVColumn(
        column_header="Website URL",
        source_class=Case,
        source_attr="home_page_url",
        required=True,
        data_type="url",
        edit_url_class=Case,
        edit_url_name="cases:edit-case-details",
    ),
    EqualityBodyCSVColumn(
        column_header="Parent organisation name",
        source_class=Case,
        source_attr="parental_organisation_name",
        edit_url_class=Case,
        edit_url_name="cases:edit-case-details",
    ),
    EqualityBodyCSVColumn(
        column_header="Sub-category",
        source_class=Case,
        source_attr="subcategory",
        edit_url_class=Case,
        edit_url_name="cases:edit-case-details",
    ),
    EqualityBodyCSVColumn(
        column_header="Website name",
        source_class=Case,
        source_attr="website_name",
        edit_url_class=Case,
        edit_url_name="cases:edit-case-details",
    ),
    EqualityBodyCSVColumn(
        column_header="Previous Case Number",
        source_class=Case,
        source_attr="previous_case_number",
        edit_url_class=Case,
        edit_url_name="cases:edit-case-details",
    ),
    EqualityBodyCSVColumn(
        column_header="Is it a complaint?",
        source_class=Case,
        source_attr="is_complaint",
        edit_url_class=Case,
        edit_url_name="cases:edit-case-details",
    ),
    EqualityBodyCSVColumn(
        column_header="Published report",
        source_class=Case,
        source_attr="published_report_url",
        required=True,
        data_type="url",
        edit_url_class=Report,
        edit_url_name="reports:report-publisher",
    ),
    EqualityBodyCSVColumn(
        column_header="Enforcement recommendation",
        source_class=Case,
        source_attr="recommendation_for_enforcement",
        required=True,
        edit_url_class=Case,
        edit_url_name="cases:edit-enforcement-recommendation",
    ),
    EqualityBodyCSVColumn(
        column_header="Enforcement recommendation notes including exemptions",
        source_class=Case,
        source_attr="recommendation_notes",
        required=True,
        data_type="markdown",
        edit_url_class=Case,
        edit_url_name="cases:edit-enforcement-recommendation",
    ),
    EqualityBodyCSVColumn(
        column_header="Summary of progress made / response from PSB",
        source_class=Case,
        source_attr="psb_progress_notes",
        data_type="markdown",
        edit_url_class=Case,
        edit_url_name="cases:edit-review-changes",
    ),
    EqualityBodyCSVColumn(
        column_header=CONTACT_DETAILS_COLUMN_HEADER,
        source_class=Case,
        source_attr=None,
        edit_url_class=Case,
        edit_url_name="cases:edit-contact-details",
        edit_url_label="Go to contact details",
    ),
    EqualityBodyCSVColumn(
        column_header=ORGANISATION_RESPONDED_COLUMN_HEADER,
        source_class=Case,
        source_attr="report_acknowledged_date",
        edit_url_class=Case,
        edit_url_name="cases:edit-report-acknowledged",
    ),
    EqualityBodyCSVColumn(
        column_header="Report sent on",
        source_class=Case,
        source_attr="report_sent_date",
        edit_url_class=Case,
        edit_url_name="cases:edit-report-sent-on",
    ),
    EqualityBodyCSVColumn(
        column_header="Report acknowledged",
        source_class=Case,
        source_attr="report_acknowledged_date",
        edit_url_class=Case,
        edit_url_name="cases:edit-report-acknowledged",
    ),
    EqualityBodyCSVColumn(
        column_header="12-week deadline",
        source_class=Case,
        source_attr="report_followup_week_12_due_date",
        edit_url_class=Case,
        edit_url_name="cases:edit-12-week-update-requested",
    ),
    EqualityBodyCSVColumn(
        column_header="Retest date",
        source_class=Case,
        source_attr="retested_website_date",
        edit_url_class=Case,
        edit_url_name="cases:edit-review-changes",
    ),
    EqualityBodyCSVColumn(
        column_header="Date when compliance decision email sent to public sector body",
        source_class=Case,
        source_attr="compliance_email_sent_date",
        edit_url_class=Case,
        edit_url_name="cases:edit-enforcement-recommendation",
    ),
    EqualityBodyCSVColumn(
        column_header="Compliance decision email sent to",
        source_class=Case,
        source_attr="compliance_decision_sent_to_email",
        edit_url_class=Case,
        edit_url_name="cases:edit-enforcement-recommendation",
    ),
    EqualityBodyCSVColumn(
        column_header="Total number of accessibility issues",
        source_class=Case,
        source_attr="total_website_issues",
        edit_url_class=Audit,
        edit_url_name="audits:audit-detail",
        edit_url_label="Go to view test",
    ),
    EqualityBodyCSVColumn(
        column_header="Number of issues fixed",
        source_class=Case,
        source_attr="total_website_issues_fixed",
        edit_url_class=Audit,
        edit_url_name="audits:audit-retest-detail",
        edit_url_label="Go to view 12-week test",
    ),
    EqualityBodyCSVColumn(
        column_header="Number of issues unfixed",
        source_class=Case,
        source_attr="total_website_issues_unfixed",
        edit_url_class=Audit,
        edit_url_name="audits:audit-retest-detail",
        edit_url_label="Go to view 12-week test",
    ),
    EqualityBodyCSVColumn(
        column_header="Issues fixed as a percentage",
        source_class=Case,
        source_attr="percentage_website_issues_fixed",
        edit_url_class=Case,
        edit_url_name=None,
    ),
    EqualityBodyCSVColumn(
        column_header="Was a accessibility statement found during initial assessment?",
        source_class=Case,
        source_attr="csv_export_statement_initially_found",
        required=True,
        edit_url_class=Audit,
        edit_url_name="audits:edit-statement-overview",
    ),
    EqualityBodyCSVColumn(
        column_header="Was a accessibility statement found during the 12-week assessment",
        source_class=Case,
        source_attr="csv_export_statement_found_at_12_week_retest",
        edit_url_class=Audit,
        edit_url_name="audits:edit-retest-statement-overview",
    ),
    EqualityBodyCSVColumn(
        column_header="Initial Accessibility Statement Decision",
        source_class=CaseCompliance,
        source_attr="statement_compliance_state_initial",
        required=True,
        default_data="Not assessed",
        edit_url_class=Audit,
        edit_url_name="audits:edit-statement-decision",
    ),
    EqualityBodyCSVColumn(
        column_header="Retest Accessibility Statement Decision",
        source_class=CaseCompliance,
        source_attr="statement_compliance_state_12_week",
        edit_url_class=Audit,
        edit_url_name="audits:edit-audit-retest-statement-decision",
    ),
    EqualityBodyCSVColumn(
        column_header="Initial disproportionate burden claim",
        source_class=Audit,
        source_attr="initial_disproportionate_burden_claim",
        edit_url_class=Audit,
        edit_url_name="audits:edit-initial-disproportionate-burden",
    ),
    EqualityBodyCSVColumn(
        column_header="Initial disproportionate burden details",
        source_class=Audit,
        source_attr="initial_disproportionate_burden_notes",
        data_type="markdown",
        edit_url_class=Audit,
        edit_url_name="audits:edit-initial-disproportionate-burden",
    ),
    EqualityBodyCSVColumn(
        column_header="Retest disproportionate burden claimed?",
        source_class=Audit,
        source_attr="twelve_week_disproportionate_burden_claim",
        edit_url_class=Audit,
        edit_url_name="audits:edit-twelve-week-disproportionate-burden",
    ),
    EqualityBodyCSVColumn(
        column_header="Retest disproportionate burden details",
        source_class=Audit,
        source_attr="twelve_week_disproportionate_burden_notes",
        data_type="markdown",
        edit_url_class=Audit,
        edit_url_name="audits:edit-twelve-week-disproportionate-burden",
    ),
]

CASE_COLUMNS_FOR_EXPORT: List[CSVColumn] = [
    CSVColumn(column_header="Case no.", source_class=Case, source_attr="id"),
    CSVColumn(column_header="Version", source_class=Case, source_attr="version"),
    CSVColumn(column_header="Created by", source_class=Case, source_attr="created_by"),
    CSVColumn(column_header="Date created", source_class=Case, source_attr="created"),
    CSVColumn(column_header="Status", source_class=CaseStatus, source_attr="status"),
    CSVColumn(column_header="Auditor", source_class=Case, source_attr="auditor"),
    CSVColumn(column_header="Type of test", source_class=Case, source_attr="test_type"),
    CSVColumn(column_header="Full URL", source_class=Case, source_attr="home_page_url"),
    CSVColumn(column_header="Domain name", source_class=Case, source_attr="domain"),
    CSVColumn(
        column_header="Organisation name",
        source_class=Case,
        source_attr="organisation_name",
    ),
    CSVColumn(
        column_header="Public sector body location",
        source_class=Case,
        source_attr="psb_location",
    ),
    CSVColumn(column_header="Sector", source_class=Case, source_attr="sector"),
    CSVColumn(
        column_header="Which equalities body will check the case?",
        source_class=Case,
        source_attr="enforcement_body",
    ),
    CSVColumn(
        column_header="Complaint?", source_class=Case, source_attr="is_complaint"
    ),
    CSVColumn(
        column_header="URL to previous case",
        source_class=Case,
        source_attr="previous_case_url",
    ),
    CSVColumn(
        column_header="Trello ticket URL", source_class=Case, source_attr="trello_url"
    ),
    CSVColumn(
        column_header="Case details notes", source_class=Case, source_attr="notes"
    ),
    CSVColumn(
        column_header="Case details page complete",
        source_class=Case,
        source_attr="case_details_complete_date",
    ),
    CSVColumn(
        column_header="Initial accessibility statement compliance decision",
        source_class=CaseCompliance,
        source_attr="statement_compliance_state_initial",
    ),
    CSVColumn(
        column_header="Initial accessibility statement compliance notes",
        source_class=CaseCompliance,
        source_attr="statement_compliance_notes_initial",
    ),
    CSVColumn(
        column_header="Initial website compliance decision",
        source_class=CaseCompliance,
        source_attr="website_compliance_state_initial",
    ),
    CSVColumn(
        column_header="Initial website compliance notes",
        source_class=CaseCompliance,
        source_attr="website_compliance_notes_initial",
    ),
    CSVColumn(
        column_header="Testing details page complete",
        source_class=Case,
        source_attr="testing_details_complete_date",
    ),
    CSVColumn(
        column_header="Link to report draft",
        source_class=Case,
        source_attr="report_draft_url",
    ),
    CSVColumn(
        column_header="Report details notes",
        source_class=Case,
        source_attr="report_notes",
    ),
    CSVColumn(
        column_header="Report details page complete",
        source_class=Case,
        source_attr="reporting_details_complete_date",
    ),
    CSVColumn(
        column_header="Report ready to be reviewed?",
        source_class=Case,
        source_attr="report_review_status",
    ),
    CSVColumn(column_header="QA auditor", source_class=Case, source_attr="reviewer"),
    CSVColumn(
        column_header="Report approved?",
        source_class=Case,
        source_attr="report_approved_status",
    ),
    CSVColumn(
        column_header="Link to final PDF report",
        source_class=Case,
        source_attr="report_final_pdf_url",
    ),
    CSVColumn(
        column_header="Link to final ODT report",
        source_class=Case,
        source_attr="report_final_odt_url",
    ),
    CSVColumn(
        column_header="QA process page complete",
        source_class=Case,
        source_attr="qa_process_complete_date",
    ),
    CSVColumn(
        column_header="Contact details page complete",
        source_class=Case,
        source_attr="contact_details_complete_date",
    ),
    CSVColumn(
        column_header="Seven day 'no contact details' email sent",
        source_class=Case,
        source_attr="seven_day_no_contact_email_sent_date",
    ),
    CSVColumn(
        column_header="Report sent on",
        source_class=Case,
        source_attr="report_sent_date",
    ),
    CSVColumn(
        column_header="1-week follow-up sent date",
        source_class=Case,
        source_attr="report_followup_week_1_sent_date",
    ),
    CSVColumn(
        column_header="4-week follow-up sent date",
        source_class=Case,
        source_attr="report_followup_week_4_sent_date",
    ),
    CSVColumn(
        column_header="Report acknowledged",
        source_class=Case,
        source_attr="report_acknowledged_date",
    ),
    CSVColumn(
        column_header="Zendesk ticket URL", source_class=Case, source_attr="zendesk_url"
    ),
    CSVColumn(
        column_header="Report correspondence notes",
        source_class=Case,
        source_attr="correspondence_notes",
    ),
    CSVColumn(
        column_header="Report correspondence page complete",
        source_class=Case,
        source_attr="report_acknowledged_complete_date",
    ),
    CSVColumn(
        column_header="1-week follow-up due date",
        source_class=Case,
        source_attr="report_followup_week_1_due_date",
    ),
    CSVColumn(
        column_header="4-week follow-up due date",
        source_class=Case,
        source_attr="report_followup_week_4_due_date",
    ),
    CSVColumn(
        column_header="12-week follow-up due date",
        source_class=Case,
        source_attr="report_followup_week_12_due_date",
    ),
    CSVColumn(
        column_header="Do you want to mark the PSB as unresponsive to this case?",
        source_class=Case,
        source_attr="no_psb_contact",
    ),
    CSVColumn(
        column_header="12-week update requested",
        source_class=Case,
        source_attr="twelve_week_update_requested_date",
    ),
    CSVColumn(
        column_header="12-week chaser 1-week follow-up sent date",
        source_class=Case,
        source_attr="twelve_week_1_week_chaser_sent_date",
    ),
    CSVColumn(
        column_header="12-week update received",
        source_class=Case,
        source_attr="twelve_week_correspondence_acknowledged_date",
    ),
    CSVColumn(
        column_header="12-week correspondence notes",
        source_class=Case,
        source_attr="twelve_week_correspondence_notes",
    ),
    CSVColumn(
        column_header="Mark the case as having no response to 12 week deadline",
        source_class=Case,
        source_attr="organisation_response",
    ),
    CSVColumn(
        column_header="12-week update request acknowledged page complete",
        source_class=Case,
        source_attr="twelve_week_update_request_ack_complete_date",
    ),
    CSVColumn(
        column_header="12-week chaser 1-week follow-up due date",
        source_class=Case,
        source_attr="twelve_week_1_week_chaser_due_date",
    ),
    CSVColumn(
        column_header="12-week retest page complete",
        source_class=Case,
        source_attr="twelve_week_retest_complete_date",
    ),
    CSVColumn(
        column_header="Summary of progress made from public sector body",
        source_class=Case,
        source_attr="psb_progress_notes",
    ),
    CSVColumn(
        column_header="Retested website?",
        source_class=Case,
        source_attr="retested_website_date",
    ),
    CSVColumn(
        column_header="Is this case ready for final decision?",
        source_class=Case,
        source_attr="is_ready_for_final_decision",
    ),
    CSVColumn(
        column_header="Reviewing changes page complete",
        source_class=Case,
        source_attr="review_changes_complete_date",
    ),
    CSVColumn(
        column_header="12-week website compliance decision",
        source_class=CaseCompliance,
        source_attr="website_compliance_state_12_week",
    ),
    CSVColumn(
        column_header="12-week website compliance decision notes",
        source_class=CaseCompliance,
        source_attr="website_compliance_notes_12_week",
    ),
    CSVColumn(
        column_header="Final website compliance decision page complete (spreadsheet testing)",
        source_class=Case,
        source_attr="final_website_complete_date",
    ),
    CSVColumn(
        column_header="Disproportionate burden claimed? (spreadsheet testing)",
        source_class=Case,
        source_attr="is_disproportionate_claimed",
    ),
    CSVColumn(
        column_header="Disproportionate burden notes (spreadsheet testing)",
        source_class=Case,
        source_attr="disproportionate_notes",
    ),
    CSVColumn(
        column_header="Link to accessibility statement screenshot (spreadsheet testing)",
        source_class=Case,
        source_attr="accessibility_statement_screenshot_url",
    ),
    CSVColumn(
        column_header="12-week accessibility statement compliance decision",
        source_class=CaseCompliance,
        source_attr="statement_compliance_state_12_week",
    ),
    CSVColumn(
        column_header="12-week accessibility statement compliance notes",
        source_class=CaseCompliance,
        source_attr="statement_compliance_notes_12_week",
    ),
    CSVColumn(
        column_header="Final accessibility statement compliance decision page complete (spreadsheet testing)",
        source_class=Case,
        source_attr="final_statement_complete_date",
    ),
    CSVColumn(
        column_header="Recommendation for equality body",
        source_class=Case,
        source_attr="recommendation_for_enforcement",
    ),
    CSVColumn(
        column_header="Enforcement recommendation notes including exemptions",
        source_class=Case,
        source_attr="recommendation_notes",
    ),
    CSVColumn(
        column_header="Date when compliance decision email sent to public sector body",
        source_class=Case,
        source_attr="compliance_email_sent_date",
    ),
    CSVColumn(
        column_header="Case completed", source_class=Case, source_attr="case_completed"
    ),
    CSVColumn(
        column_header="Date case completed first updated",
        source_class=Case,
        source_attr="completed_date",
    ),
    CSVColumn(
        column_header="Closing the case page complete",
        source_class=Case,
        source_attr="case_close_complete_date",
    ),
    CSVColumn(
        column_header="Public sector body statement appeal notes",
        source_class=Case,
        source_attr="psb_appeal_notes",
    ),
    CSVColumn(
        column_header="Summary of events after the case was closed",
        source_class=Case,
        source_attr="post_case_notes",
    ),
    CSVColumn(
        column_header="Post case summary page complete",
        source_class=Case,
        source_attr="post_case_complete_date",
    ),
    CSVColumn(
        column_header="Case updated (on post case summary page)",
        source_class=Case,
        source_attr="case_updated_date",
    ),
    CSVColumn(
        column_header="Date sent to equality body",
        source_class=Case,
        source_attr="sent_to_enforcement_body_sent_date",
    ),
    CSVColumn(
        column_header="Equality body pursuing this case?",
        source_class=Case,
        source_attr="enforcement_body_pursuing",
    ),
    CSVColumn(
        column_header="Equality body correspondence notes",
        source_class=Case,
        source_attr="enforcement_body_correspondence_notes",
    ),
    CSVColumn(
        column_header="Equality body summary page complete",
        source_class=Case,
        source_attr="enforcement_correspondence_complete_date",
    ),
    CSVColumn(
        column_header="Deactivated case",
        source_class=Case,
        source_attr="is_deactivated",
    ),
    CSVColumn(
        column_header="Date deactivated",
        source_class=Case,
        source_attr="deactivate_date",
    ),
    CSVColumn(
        column_header="Reason why (deactivated)",
        source_class=Case,
        source_attr="deactivate_notes",
    ),
    CSVColumn(column_header="QA status", source_class=Case, source_attr="qa_status"),
    CSVColumn(
        column_header="Contact detail notes",
        source_class=Case,
        source_attr="contact_notes",
    ),
    CSVColumn(
        column_header="Date equality body completed the case",
        source_class=Case,
        source_attr="enforcement_body_finished_date",
    ),
    CSVColumn(
        column_header="% of issues fixed",
        source_class=Case,
        source_attr="percentage_website_issues_fixed",
    ),
    CSVColumn(
        column_header="Parental organisation name",
        source_class=Case,
        source_attr="parental_organisation_name",
    ),
    CSVColumn(
        column_header="Website name", source_class=Case, source_attr="website_name"
    ),
    CSVColumn(
        column_header="Sub-category", source_class=Case, source_attr="subcategory"
    ),
    CSVColumn(column_header="Contact email", source_class=Contact, source_attr="email"),
]

FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT: List[CSVColumn] = [
    CSVColumn(column_header="Case no.", source_class=Case, source_attr="id"),
    CSVColumn(
        column_header="Organisation name",
        source_class=Case,
        source_attr="organisation_name",
    ),
    CSVColumn(
        column_header="Closing the case date",
        source_class=Case,
        source_attr="compliance_email_sent_date",
    ),
    CSVColumn(
        column_header="Enforcement recommendation",
        source_class=Case,
        source_attr="recommendation_for_enforcement",
    ),
    CSVColumn(
        column_header="Enforcement recommendation notes",
        source_class=Case,
        source_attr="recommendation_notes",
    ),
    CSVColumn(column_header="Contact email", source_class=Contact, source_attr="email"),
    CSVColumn(
        column_header="Contact notes", source_class=Case, source_attr="contact_notes"
    ),
    CSVColumn(
        column_header="Feedback survey sent?",
        source_class=Case,
        source_attr="is_feedback_requested",
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
    sort_by: str = Sort.NEWEST

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
        sort_by: str = form.cleaned_data.get("sort_by", Sort.NEWEST)
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
                    | Q(parental_organisation_name__icontains=search)
                    | Q(website_name__icontains=search)
                    | Q(subcategory__name__icontains=search)
                )
        for filter_name in ["is_complaint", "enforcement_body"]:
            filter_value: str = form.cleaned_data.get(filter_name, Complaint.ALL)
            if filter_value != Complaint.ALL:
                filters[filter_name] = filter_value

    if str(filters.get("status", "")) == CaseStatus.Status.READY_TO_QA:
        filters["qa_status"] = CaseStatus.Status.READY_TO_QA
        del filters["status"]

    if "status" in filters:
        filters["status__status"] = filters["status"]
        del filters["status"]

    # Auditor and reviewer may be filtered by unassigned
    if "auditor_id" in filters and filters["auditor_id"] == "none":
        filters["auditor_id"] = None
    if "reviewer_id" in filters and filters["reviewer_id"] == "none":
        filters["reviewer_id"] = None

    if not sort_by:
        return (
            Case.objects.filter(search_query, **filters)
            .annotate(
                position_unassigned_first=DjangoCase(
                    When(status__status=CaseStatus.Status.UNASSIGNED, then=0), default=1
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


def format_contacts(contacts: QuerySet[Contact]) -> str:
    """
    For a contact-related field, concatenate the values for all the contacts
    and return as a single string.
    """
    contact_details: str = ""
    for contact in contacts:
        if contact_details:
            contact_details += "\n"
        if contact.name:
            contact_details += f"{contact.name}\n"
        if contact.job_title:
            contact_details += f"{contact.job_title}\n"
        if contact.email:
            contact_details += f"{contact.email}\n"
    return contact_details


def format_field_as_yes_no(
    source_instance: Union[Audit, Case, Contact, None], column: CSVColumn
) -> str:
    """
    If the field contains a truthy value return Yes otherwise return No.
    """
    if source_instance is None:
        return "No"
    value: Any = getattr(source_instance, column.source_attr, False)
    if value:
        return "Yes"
    return "No"


def format_model_field(
    source_instance: Union[Audit, Case, Contact, None], column: CSVColumn
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


def populate_equality_body_columns(case: Case) -> List[EqualityBodyCSVColumn]:
    """
    Collect data for a case to export to the equality body
    """
    contact_details: str = format_contacts(contacts=case.contacts)
    source_instances: Dict = {
        Case: case,
        Audit: case.audit,
        CaseCompliance: case.compliance,
        Report: case.report,
    }
    columns: List[EqualityBodyCSVColumn] = EQUALITY_BODY_COLUMNS_FOR_EXPORT.copy()
    for column in columns:
        source_instance: Union[
            Audit, Case, CaseCompliance, Report
        ] = source_instances.get(column.source_class)
        edit_url_instance: Union[
            Audit, Case, CaseCompliance, Report
        ] = source_instances.get(column.edit_url_class)
        if column.column_header == CONTACT_DETAILS_COLUMN_HEADER:
            column.formatted_data = contact_details
        elif column.column_header == ORGANISATION_RESPONDED_COLUMN_HEADER:
            column.formatted_data = format_field_as_yes_no(
                source_instance=case, column=column
            )
        else:
            column.formatted_data = format_model_field(
                source_instance=source_instance, column=column
            )
        if column.edit_url_name is not None and edit_url_instance is not None:
            column.edit_url = reverse(
                column.edit_url_name, kwargs={"pk": edit_url_instance.id}
            )
    return columns


def download_equality_body_cases(
    cases: QuerySet[Case],
    filename: str = "ehrc_cases.csv",
) -> HttpResponse:
    """Given a Case queryset, download the data in csv format for equality body"""
    response: Any = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"

    writer: Any = csv.writer(response)
    writer.writerow(
        [column.column_header for column in EQUALITY_BODY_COLUMNS_FOR_EXPORT]
    )

    output: List[List[str]] = []
    for case in cases:
        case_columns: List[EqualityBodyCSVColumn] = populate_equality_body_columns(
            case=case
        )
        row = [column.formatted_data for column in case_columns]
        output.append(row)
    writer.writerows(output)

    return response


def populate_csv_columns(
    case: Case, column_definitions: List[CSVColumn]
) -> List[CSVColumn]:
    """
    Collect data for a case to export
    """
    source_instances: Dict = {
        Case: case,
        CaseCompliance: case.compliance,
        CaseStatus: case.status,
        Contact: case.contact_set.filter(is_deleted=False).first(),
    }
    columns: List[CSVColumn] = column_definitions.copy()
    for column in columns:
        source_instance: Union[
            Case, CaseCompliance, CaseStatus, Contact, None
        ] = source_instances.get(column.source_class)
        column.formatted_data = format_model_field(
            source_instance=source_instance, column=column
        )
    return columns


def download_cases(cases: QuerySet[Case], filename: str = "cases.csv") -> HttpResponse:
    """Given a Case queryset, download the data in csv format"""
    response: Any = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"

    writer: Any = csv.writer(response)
    writer.writerow([column.column_header for column in CASE_COLUMNS_FOR_EXPORT])

    output: List[List[str]] = []
    for case in cases:
        case_columns: List[CSVColumn] = populate_csv_columns(
            case=case, column_definitions=CASE_COLUMNS_FOR_EXPORT
        )
        row = [column.formatted_data for column in case_columns]
        output.append(row)
    writer.writerows(output)

    return response


def download_feedback_survey_cases(
    cases: QuerySet[Case], filename: str = "feedback_survey_cases.csv"
) -> HttpResponse:
    """Given a Case queryset, download the feedback survey data in csv format"""
    response: Any = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"

    writer: Any = csv.writer(response)
    writer.writerow(
        [column.column_header for column in FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT]
    )

    output: List[List[str]] = []
    for case in cases:
        case_columns: List[CSVColumn] = populate_csv_columns(
            case=case, column_definitions=FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT
        )
        row = [column.formatted_data for column in case_columns]
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
            case=new_case, done_by=user, event_type=CaseEvent.EventType.CREATE
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
            event_type=CaseEvent.EventType.AUDITOR,
            message=f"Auditor changed from {old_user_name} to {new_user_name}",
        )
    if old_case.audit is None and new_case.audit is not None:
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.CREATE_AUDIT,
            message="Start of test",
        )
    if old_case.report_review_status != new_case.report_review_status:
        old_status: str = old_case.get_report_review_status_display()
        new_status: str = new_case.get_report_review_status_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.READY_FOR_QA,
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
            event_type=CaseEvent.EventType.QA_AUDITOR,
            message=f"QA auditor changed from {old_user_name} to {new_user_name}",
        )
    if old_case.report_approved_status != new_case.report_approved_status:
        old_status: str = old_case.get_report_approved_status_display()
        new_status: str = new_case.get_report_approved_status_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.APPROVE_REPORT,
            message=f"Report approved changed from '{old_status}' to '{new_status}'",
        )
    if old_case.is_ready_for_final_decision != new_case.is_ready_for_final_decision:
        old_status: str = old_case.get_is_ready_for_final_decision_display()
        new_status: str = new_case.get_is_ready_for_final_decision_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.READY_FOR_FINAL_DECISION,
            message=f"Case ready for final decision changed from '{old_status}' to '{new_status}'",
        )
    if old_case.case_completed != new_case.case_completed:
        old_status: str = old_case.get_case_completed_display()
        new_status: str = new_case.get_case_completed_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.CASE_COMPLETED,
            message=f"Case completed changed from '{old_status}' to '{new_status}'",
        )


def build_edit_link_html(case: Case, url_name: str) -> str:
    """Return html of edit link for case"""
    case_pk: Dict[str, int] = {"pk": case.id}
    edit_url: str = reverse(url_name, kwargs=case_pk)
    return (
        f"<a href='{edit_url}' class='govuk-link govuk-link--no-visited-state'>Edit</a>"
    )


def create_case_and_compliance(**kwargs):
    """Create case and populate compliance fields from arbitrary arguments"""
    compliance_kwargs: Dict[str, Any] = {
        key: value for key, value in kwargs.items() if key in COMPLIANCE_FIELDS
    }
    non_compliance_args: Dict[str, Any] = {
        key: value for key, value in kwargs.items() if key not in COMPLIANCE_FIELDS
    }
    case: Case = Case.objects.create(**non_compliance_args)
    if compliance_kwargs:
        for key, value in compliance_kwargs.items():
            setattr(case.compliance, key, value)
        case.compliance.save()
        case.save()
    return case


def get_post_case_alerts_count(user: User) -> int:
    """
    Return the number of unresolved equality body correspondence entries
    and incomplete equality body retests for user.
    """
    if user.id:
        return (
            EqualityBodyCorrespondence.objects.filter(
                case__auditor=user, status=EqualityBodyCorrespondence.Status.UNRESOLVED
            ).count()
            + Retest.objects.filter(
                is_deleted=False,
                case__auditor=user,
                retest_compliance_state=Retest.Compliance.NOT_KNOWN,
                id_within_case__gt=0,
            ).count()
        )
    return 0


def get_post_case_alerts(user: User) -> List[PostCaseAlert]:
    """
    Return sorted list of unresolved equality body correspondence entries and
    incomplete equality body retests for a user.
    """
    post_case_alerts: List[PostCaseAlert] = []

    equality_body_correspondences: QuerySet[
        EqualityBodyCorrespondence
    ] = EqualityBodyCorrespondence.objects.filter(
        case__auditor=user,
        status=EqualityBodyCorrespondence.Status.UNRESOLVED,
    )

    for equality_body_correspondence in equality_body_correspondences:
        post_case_alerts.append(
            PostCaseAlert(
                date=equality_body_correspondence.created.date(),
                case=equality_body_correspondence.case,
                description="Unresolved correspondence",
                absolute_url=f"{equality_body_correspondence.get_absolute_url()}?view=unresolved",
                absolute_url_label="View correspondence",
            )
        )

    retests: QuerySet[Retest] = Retest.objects.filter(
        is_deleted=False,
        case__auditor=user,
        retest_compliance_state=Retest.Compliance.NOT_KNOWN,
        id_within_case__gt=0,
    )

    for retest in retests:
        post_case_alerts.append(
            PostCaseAlert(
                date=retest.date_of_retest,
                case=retest.case,
                description="Incomplete retest",
                absolute_url=retest.get_absolute_url(),
                absolute_url_label="View retest",
            )
        )
    return sorted(post_case_alerts, key=lambda alert: alert.date, reverse=True)
