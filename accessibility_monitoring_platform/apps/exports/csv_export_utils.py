"""
Utility functions for cases app
"""

import copy
import csv
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Generator, Literal

from django.db.models import QuerySet
from django.http import StreamingHttpResponse
from django.urls import reverse

from ..audits.models import Audit
from ..reports.models import Report
from ..simplified.models import CaseCompliance, CaseStatus, Contact, SimplifiedCase

DOWNLOAD_CASES_CHUNK_SIZE: int = 500


@dataclass
class CSVColumn:
    """Data to use when building export CSV"""

    column_header: str
    source_class: Audit | SimplifiedCase | CaseCompliance
    source_attr: str


@dataclass
class EqualityBodyCSVColumn(CSVColumn):
    """Data to use when building export CSV for equality body and to show in UI"""

    data_type: Literal["str", "url", "markdown", "pre"] = "str"
    required: bool = False
    formatted_data: str = ""
    default_data: str = ""
    ui_suffix: str = ""
    edit_url_class: Audit | SimplifiedCase | CaseCompliance | Report | None = None
    edit_url_name: str | None = None
    edit_url_label: str = "Edit"
    edit_url_anchor: str = ""
    edit_url: str | None = None

    @property
    def required_data_missing(self):
        return self.required and (
            self.formatted_data is None or self.formatted_data == self.default_data
        )


CONTACT_DETAILS_COLUMN_HEADER: str = "Contact details"

EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = [
    EqualityBodyCSVColumn(
        column_header="Equality body",
        source_class=SimplifiedCase,
        source_attr="enforcement_body",
        required=True,
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-case-metadata",
        edit_url_anchor="id_enforcement_body-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Test type",
        source_class=SimplifiedCase,
        source_attr="test_type",
        required=True,
        edit_url_class=SimplifiedCase,
        edit_url_name=None,
    ),
    EqualityBodyCSVColumn(
        column_header="Case number",
        source_class=SimplifiedCase,
        source_attr="case_number",
        required=True,
        edit_url_class=SimplifiedCase,
        edit_url_name=None,
    ),
    EqualityBodyCSVColumn(
        column_header="Organisation",
        source_class=SimplifiedCase,
        source_attr="organisation_name",
        required=True,
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-case-metadata",
        edit_url_anchor="id_organisation_name-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Website URL",
        source_class=SimplifiedCase,
        source_attr="home_page_url",
        required=True,
        data_type="url",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-case-metadata",
        edit_url_anchor="id_home_page_url-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Parent organisation name",
        source_class=SimplifiedCase,
        source_attr="parental_organisation_name",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-case-metadata",
        edit_url_anchor="id_parental_organisation_name-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Sub-category",
        source_class=SimplifiedCase,
        source_attr="subcategory",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-case-metadata",
        edit_url_anchor="id_subcategory-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Website name",
        source_class=SimplifiedCase,
        source_attr="website_name",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-case-metadata",
        edit_url_anchor="id_website_name-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Previous Case Number",
        source_class=SimplifiedCase,
        source_attr="previous_case_number",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-case-metadata",
        edit_url_anchor="id_previous_case_url-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Is it a complaint?",
        source_class=SimplifiedCase,
        source_attr="is_complaint",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-case-metadata",
        edit_url_anchor="id_is_complaint-label",
    ),
]
EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = [
    EqualityBodyCSVColumn(
        column_header="Published report",
        source_class=SimplifiedCase,
        source_attr="published_report_url",
        required=True,
        data_type="url",
        edit_url_class=Report,
        edit_url_name="reports:report-preview",
    ),
    EqualityBodyCSVColumn(
        column_header="Enforcement recommendation",
        source_class=SimplifiedCase,
        source_attr="recommendation_for_enforcement",
        required=True,
        default_data="Not selected",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-enforcement-recommendation",
        edit_url_anchor="id_recommendation_for_enforcement-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Enforcement recommendation notes including exemptions",
        source_class=SimplifiedCase,
        source_attr="recommendation_notes",
        required=True,
        data_type="markdown",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-enforcement-recommendation",
        edit_url_anchor="id_recommendation_notes-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Summary of progress made / response from PSB",
        source_class=SimplifiedCase,
        source_attr="psb_progress_notes",
        data_type="markdown",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-review-changes",
        edit_url_anchor="id_psb_progress_notes-label",
    ),
]
EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = [
    EqualityBodyCSVColumn(
        column_header=CONTACT_DETAILS_COLUMN_HEADER,
        source_class=SimplifiedCase,
        source_attr=None,
        data_type="pre",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:manage-contact-details",
        edit_url_label="Go to contact details",
    ),
    EqualityBodyCSVColumn(
        column_header="Organisation responded to report?",
        source_class=SimplifiedCase,
        source_attr="report_acknowledged_yes_no",
        ui_suffix=" (derived from report acknowledged date)",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-report-acknowledged",
        edit_url_anchor="id_report_acknowledged_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Report sent on",
        source_class=SimplifiedCase,
        source_attr="report_sent_date",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-report-sent-on",
        edit_url_anchor="id_report_sent_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Report acknowledged",
        source_class=SimplifiedCase,
        source_attr="report_acknowledged_date",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-report-acknowledged",
        edit_url_anchor="id_report_acknowledged_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="12-week deadline",
        source_class=SimplifiedCase,
        source_attr="report_followup_week_12_due_date",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-12-week-update-requested",
        edit_url_anchor="id_twelve_week_update_requested_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Retest date",
        source_class=SimplifiedCase,
        source_attr="retested_website_date",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-review-changes",
        edit_url_anchor="id_retested_website_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Date when compliance decision email sent to public sector body",
        source_class=SimplifiedCase,
        source_attr="compliance_email_sent_date",
        required=True,
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-enforcement-recommendation",
        edit_url_anchor="id_compliance_email_sent_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Compliance decision email sent to",
        source_class=SimplifiedCase,
        source_attr="compliance_decision_sent_to_email",
        edit_url_class=SimplifiedCase,
        edit_url_name="simplified:edit-enforcement-recommendation",
        edit_url_anchor="id_compliance_decision_sent_to_email-label",
    ),
]
EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = [
    EqualityBodyCSVColumn(
        column_header="Total number of accessibility issues",
        source_class=SimplifiedCase,
        source_attr="total_website_issues",
        edit_url_class=Audit,
        edit_url_name="simplified:case-detail",
        edit_url_label="Go to view test",
    ),
    EqualityBodyCSVColumn(
        column_header="Number of issues fixed",
        source_class=SimplifiedCase,
        source_attr="total_website_issues_fixed",
        edit_url_class=Audit,
        edit_url_name="audits:edit-audit-retest-metadata",
        edit_url_label="Go to view 12-week test",
    ),
    EqualityBodyCSVColumn(
        column_header="Number of issues unfixed",
        source_class=SimplifiedCase,
        source_attr="total_website_issues_unfixed",
        edit_url_class=Audit,
        edit_url_name="audits:edit-audit-retest-metadata",
        edit_url_label="Go to view 12-week test",
    ),
    EqualityBodyCSVColumn(
        column_header="Issues fixed as a percentage",
        source_class=SimplifiedCase,
        source_attr="percentage_website_issues_fixed",
        ui_suffix="% (Derived from retest results)",
        edit_url_class=SimplifiedCase,
        edit_url_name=None,
    ),
    EqualityBodyCSVColumn(
        column_header="Was an accessibility statement found during the 12-week assessment",
        source_class=SimplifiedCase,
        source_attr="csv_export_statement_found_at_12_week_retest",
        edit_url_class=Audit,
        edit_url_name="audits:edit-retest-statement-overview",
    ),
    EqualityBodyCSVColumn(
        column_header="Retest Accessibility Statement Decision",
        source_class=CaseCompliance,
        source_attr="statement_compliance_state_12_week",
        edit_url_class=Audit,
        edit_url_name="audits:edit-audit-retest-statement-decision",
        edit_url_anchor="id_case-compliance-statement_compliance_state_12_week-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Retest disproportionate burden claimed?",
        source_class=Audit,
        source_attr="twelve_week_disproportionate_burden_claim",
        edit_url_class=Audit,
        edit_url_name="audits:edit-twelve-week-disproportionate-burden",
        edit_url_anchor="id_twelve_week_disproportionate_burden_claim-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Retest disproportionate burden details",
        source_class=Audit,
        source_attr="twelve_week_disproportionate_burden_notes",
        data_type="markdown",
        edit_url_class=Audit,
        edit_url_name="audits:edit-twelve-week-disproportionate-burden",
        edit_url_anchor="id_twelve_week_disproportionate_burden_notes-label",
    ),
]
EQUALITY_BODY_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = (
    EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT
    + EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT
    + EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT
    + EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT
)

CASE_COLUMNS_FOR_EXPORT: list[CSVColumn] = [
    CSVColumn(
        column_header="Case no.", source_class=SimplifiedCase, source_attr="case_number"
    ),
    CSVColumn(
        column_header="Version", source_class=SimplifiedCase, source_attr="version"
    ),
    CSVColumn(
        column_header="Created by",
        source_class=SimplifiedCase,
        source_attr="created_by",
    ),
    CSVColumn(
        column_header="Date created", source_class=SimplifiedCase, source_attr="created"
    ),
    CSVColumn(
        column_header="Status", source_class=SimplifiedCase, source_attr="status"
    ),
    CSVColumn(
        column_header="Auditor", source_class=SimplifiedCase, source_attr="auditor"
    ),
    CSVColumn(
        column_header="Type of test",
        source_class=SimplifiedCase,
        source_attr="test_type",
    ),
    CSVColumn(
        column_header="Full URL",
        source_class=SimplifiedCase,
        source_attr="home_page_url",
    ),
    CSVColumn(
        column_header="Domain name", source_class=SimplifiedCase, source_attr="domain"
    ),
    CSVColumn(
        column_header="Organisation name",
        source_class=SimplifiedCase,
        source_attr="organisation_name",
    ),
    CSVColumn(
        column_header="Public sector body location",
        source_class=SimplifiedCase,
        source_attr="psb_location",
    ),
    CSVColumn(
        column_header="Sector", source_class=SimplifiedCase, source_attr="sector"
    ),
    CSVColumn(
        column_header="Which equalities body will check the case?",
        source_class=SimplifiedCase,
        source_attr="enforcement_body",
    ),
    CSVColumn(
        column_header="Complaint?",
        source_class=SimplifiedCase,
        source_attr="is_complaint",
    ),
    CSVColumn(
        column_header="URL to previous case",
        source_class=SimplifiedCase,
        source_attr="previous_case_url",
    ),
    CSVColumn(
        column_header="Trello ticket URL",
        source_class=SimplifiedCase,
        source_attr="trello_url",
    ),
    CSVColumn(
        column_header="Case details notes",
        source_class=SimplifiedCase,
        source_attr="notes",
    ),
    CSVColumn(
        column_header="Case details page complete",
        source_class=SimplifiedCase,
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
        source_class=SimplifiedCase,
        source_attr="reporting_details_complete_date",
    ),
    CSVColumn(
        column_header="Link to report draft",
        source_class=SimplifiedCase,
        source_attr="report_draft_url",
    ),
    CSVColumn(
        column_header="Report details notes",
        source_class=SimplifiedCase,
        source_attr="report_notes",
    ),
    CSVColumn(
        column_header="Report details page complete",
        source_class=SimplifiedCase,
        source_attr="reporting_details_complete_date",
    ),
    CSVColumn(
        column_header="Report ready to be reviewed?",
        source_class=SimplifiedCase,
        source_attr="report_review_status",
    ),
    CSVColumn(
        column_header="QA auditor", source_class=SimplifiedCase, source_attr="reviewer"
    ),
    CSVColumn(
        column_header="Report approved?",
        source_class=SimplifiedCase,
        source_attr="report_approved_status",
    ),
    CSVColumn(
        column_header="Link to final PDF report",
        source_class=SimplifiedCase,
        source_attr="report_final_pdf_url",
    ),
    CSVColumn(
        column_header="Link to final ODT report",
        source_class=SimplifiedCase,
        source_attr="report_final_odt_url",
    ),
    CSVColumn(
        column_header="QA process page complete",
        source_class=SimplifiedCase,
        source_attr="qa_process_complete_date",
    ),
    CSVColumn(
        column_header="Contact details page complete",
        source_class=SimplifiedCase,
        source_attr="manage_contact_details_complete_date",
    ),
    CSVColumn(
        column_header="Seven day 'no contact details' email sent",
        source_class=SimplifiedCase,
        source_attr="seven_day_no_contact_email_sent_date",
    ),
    CSVColumn(
        column_header="Report sent on",
        source_class=SimplifiedCase,
        source_attr="report_sent_date",
    ),
    CSVColumn(
        column_header="1-week follow-up sent date",
        source_class=SimplifiedCase,
        source_attr="report_followup_week_1_sent_date",
    ),
    CSVColumn(
        column_header="4-week follow-up sent date",
        source_class=SimplifiedCase,
        source_attr="report_followup_week_4_sent_date",
    ),
    CSVColumn(
        column_header="Report acknowledged",
        source_class=SimplifiedCase,
        source_attr="report_acknowledged_date",
    ),
    CSVColumn(
        column_header="Zendesk ticket URL",
        source_class=SimplifiedCase,
        source_attr="zendesk_url",
    ),
    CSVColumn(
        column_header="Report correspondence notes",
        source_class=SimplifiedCase,
        source_attr="correspondence_notes",
    ),
    CSVColumn(
        column_header="Report correspondence page complete",
        source_class=SimplifiedCase,
        source_attr="report_acknowledged_complete_date",
    ),
    CSVColumn(
        column_header="1-week follow-up due date",
        source_class=SimplifiedCase,
        source_attr="report_followup_week_1_due_date",
    ),
    CSVColumn(
        column_header="4-week follow-up due date",
        source_class=SimplifiedCase,
        source_attr="report_followup_week_4_due_date",
    ),
    CSVColumn(
        column_header="12-week follow-up due date",
        source_class=SimplifiedCase,
        source_attr="report_followup_week_12_due_date",
    ),
    CSVColumn(
        column_header="Do you want to mark the PSB as unresponsive to this case?",
        source_class=SimplifiedCase,
        source_attr="no_psb_contact",
    ),
    CSVColumn(
        column_header="12-week update requested",
        source_class=SimplifiedCase,
        source_attr="twelve_week_update_requested_date",
    ),
    CSVColumn(
        column_header="12-week chaser 1-week follow-up sent date",
        source_class=SimplifiedCase,
        source_attr="twelve_week_1_week_chaser_sent_date",
    ),
    CSVColumn(
        column_header="12-week update received",
        source_class=SimplifiedCase,
        source_attr="twelve_week_correspondence_acknowledged_date",
    ),
    CSVColumn(
        column_header="12-week correspondence notes",
        source_class=SimplifiedCase,
        source_attr="twelve_week_correspondence_notes",
    ),
    CSVColumn(
        column_header="Mark the case as having no response to 12 week deadline",
        source_class=SimplifiedCase,
        source_attr="organisation_response",
    ),
    CSVColumn(
        column_header="12-week update request acknowledged page complete",
        source_class=SimplifiedCase,
        source_attr="twelve_week_update_request_ack_complete_date",
    ),
    CSVColumn(
        column_header="12-week chaser 1-week follow-up due date",
        source_class=SimplifiedCase,
        source_attr="twelve_week_1_week_chaser_due_date",
    ),
    CSVColumn(
        column_header="12-week retest page complete",
        source_class=SimplifiedCase,
        source_attr="twelve_week_retest_complete_date",
    ),
    CSVColumn(
        column_header="Summary of progress made from public sector body",
        source_class=SimplifiedCase,
        source_attr="psb_progress_notes",
    ),
    CSVColumn(
        column_header="Retested website?",
        source_class=SimplifiedCase,
        source_attr="retested_website_date",
    ),
    CSVColumn(
        column_header="Is this case ready for final decision?",
        source_class=SimplifiedCase,
        source_attr="is_ready_for_final_decision",
    ),
    CSVColumn(
        column_header="Reviewing changes page complete",
        source_class=SimplifiedCase,
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
        source_class=SimplifiedCase,
        source_attr="final_website_complete_date",
    ),
    CSVColumn(
        column_header="Disproportionate burden claimed? (spreadsheet testing)",
        source_class=SimplifiedCase,
        source_attr="is_disproportionate_claimed",
    ),
    CSVColumn(
        column_header="Disproportionate burden notes (spreadsheet testing)",
        source_class=SimplifiedCase,
        source_attr="disproportionate_notes",
    ),
    CSVColumn(
        column_header="Link to accessibility statement screenshot (spreadsheet testing)",
        source_class=SimplifiedCase,
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
        source_class=SimplifiedCase,
        source_attr="final_statement_complete_date",
    ),
    CSVColumn(
        column_header="Recommendation for equality body",
        source_class=SimplifiedCase,
        source_attr="recommendation_for_enforcement",
    ),
    CSVColumn(
        column_header="Enforcement recommendation notes including exemptions",
        source_class=SimplifiedCase,
        source_attr="recommendation_notes",
    ),
    CSVColumn(
        column_header="Date when compliance decision email sent to public sector body",
        source_class=SimplifiedCase,
        source_attr="compliance_email_sent_date",
    ),
    CSVColumn(
        column_header="Case completed",
        source_class=SimplifiedCase,
        source_attr="case_completed",
    ),
    CSVColumn(
        column_header="Date case completed first updated",
        source_class=SimplifiedCase,
        source_attr="completed_date",
    ),
    CSVColumn(
        column_header="Closing the case page complete",
        source_class=SimplifiedCase,
        source_attr="case_close_complete_date",
    ),
    CSVColumn(
        column_header="Public sector body statement appeal notes",
        source_class=SimplifiedCase,
        source_attr="psb_appeal_notes",
    ),
    CSVColumn(
        column_header="Summary of events after the case was closed",
        source_class=SimplifiedCase,
        source_attr="post_case_notes",
    ),
    CSVColumn(
        column_header="Post case summary page complete",
        source_class=SimplifiedCase,
        source_attr="post_case_complete_date",
    ),
    CSVColumn(
        column_header="Case updated (on post case summary page)",
        source_class=SimplifiedCase,
        source_attr="case_updated_date",
    ),
    CSVColumn(
        column_header="Date sent to equality body",
        source_class=SimplifiedCase,
        source_attr="sent_to_enforcement_body_sent_date",
    ),
    CSVColumn(
        column_header="Equality body pursuing this case?",
        source_class=SimplifiedCase,
        source_attr="enforcement_body_pursuing",
    ),
    CSVColumn(
        column_header="Equality body correspondence notes",
        source_class=SimplifiedCase,
        source_attr="enforcement_body_correspondence_notes",
    ),
    CSVColumn(
        column_header="Equality body summary page complete",
        source_class=SimplifiedCase,
        source_attr="enforcement_correspondence_complete_date",
    ),
    CSVColumn(
        column_header="Deactivated case",
        source_class=SimplifiedCase,
        source_attr="is_deactivated",
    ),
    CSVColumn(
        column_header="Date deactivated",
        source_class=SimplifiedCase,
        source_attr="deactivate_date",
    ),
    CSVColumn(
        column_header="Reason why (deactivated)",
        source_class=SimplifiedCase,
        source_attr="deactivate_notes",
    ),
    CSVColumn(
        column_header="QA status", source_class=SimplifiedCase, source_attr="qa_status"
    ),
    CSVColumn(
        column_header="Contact detail notes",
        source_class=SimplifiedCase,
        source_attr="contact_notes",
    ),
    CSVColumn(
        column_header="Date equality body completed the case",
        source_class=SimplifiedCase,
        source_attr="enforcement_body_finished_date",
    ),
    CSVColumn(
        column_header="% of issues fixed",
        source_class=SimplifiedCase,
        source_attr="percentage_website_issues_fixed",
    ),
    CSVColumn(
        column_header="Parental organisation name",
        source_class=SimplifiedCase,
        source_attr="parental_organisation_name",
    ),
    CSVColumn(
        column_header="Website name",
        source_class=SimplifiedCase,
        source_attr="website_name",
    ),
    CSVColumn(
        column_header="Sub-category",
        source_class=SimplifiedCase,
        source_attr="subcategory",
    ),
    CSVColumn(column_header="Contact email", source_class=Contact, source_attr="email"),
]

FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT: list[CSVColumn] = [
    CSVColumn(
        column_header="Case no.", source_class=SimplifiedCase, source_attr="case_number"
    ),
    CSVColumn(
        column_header="Organisation name",
        source_class=SimplifiedCase,
        source_attr="organisation_name",
    ),
    CSVColumn(
        column_header="Closing the case date",
        source_class=SimplifiedCase,
        source_attr="compliance_email_sent_date",
    ),
    CSVColumn(
        column_header="Enforcement recommendation",
        source_class=SimplifiedCase,
        source_attr="recommendation_for_enforcement",
    ),
    CSVColumn(
        column_header="Enforcement recommendation notes",
        source_class=SimplifiedCase,
        source_attr="recommendation_notes",
    ),
    CSVColumn(
        column_header="Final statement decision",
        source_class=CaseCompliance,
        source_attr="statement_compliance_state_12_week",
    ),
    CSVColumn(column_header="Contact email", source_class=Contact, source_attr="email"),
    CSVColumn(
        column_header="Contact notes",
        source_class=SimplifiedCase,
        source_attr="contact_notes",
    ),
    CSVColumn(
        column_header="Feedback survey sent?",
        source_class=SimplifiedCase,
        source_attr="is_feedback_requested",
    ),
]


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


def format_model_field(
    source_instance: Audit | SimplifiedCase | Contact | None, column: CSVColumn
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


def populate_equality_body_columns(
    simplified_case: SimplifiedCase,
    column_definitions: list[CSVColumn] = EQUALITY_BODY_COLUMNS_FOR_EXPORT,
) -> list[EqualityBodyCSVColumn]:
    """
    Collect data for a case to export to the equality body
    """
    contact_details: str = format_contacts(contacts=simplified_case.contacts)
    source_instances: dict = {
        SimplifiedCase: simplified_case,
        Audit: simplified_case.audit,
        CaseCompliance: simplified_case.compliance,
        Report: simplified_case.report,
    }
    columns: list[EqualityBodyCSVColumn] = copy.deepcopy(column_definitions)
    for column in columns:
        source_instance: Audit | SimplifiedCase | CaseCompliance | Report | None = (
            source_instances.get(column.source_class)
        )
        edit_url_instance: Audit | SimplifiedCase | CaseCompliance | Report | None = (
            source_instances.get(column.edit_url_class)
        )
        if column.column_header == CONTACT_DETAILS_COLUMN_HEADER:
            column.formatted_data = contact_details
        else:
            column.formatted_data = format_model_field(
                source_instance=source_instance, column=column
            )
        if column.edit_url_name is not None and edit_url_instance is not None:
            column.edit_url = reverse(
                column.edit_url_name, kwargs={"pk": edit_url_instance.id}
            )
            if column.edit_url_anchor:
                column.edit_url += f"#{column.edit_url_anchor}"
    return columns


def populate_csv_columns(
    simplified_case: SimplifiedCase, column_definitions: list[CSVColumn]
) -> list[CSVColumn]:
    """
    Collect data for a case to export
    """
    source_instances: dict = {
        SimplifiedCase: simplified_case,
        CaseCompliance: simplified_case.compliance,
        CaseStatus: simplified_case.status,
        Contact: simplified_case.contact_set.filter(is_deleted=False).first(),
    }
    columns: list[CSVColumn] = copy.deepcopy(column_definitions)
    for column in columns:
        source_instance: (
            SimplifiedCase | CaseCompliance | CaseStatus | Contact | None
        ) = source_instances.get(column.source_class)
        column.formatted_data = format_model_field(
            source_instance=source_instance, column=column
        )
    return columns


def csv_output_generator(
    cases: QuerySet[SimplifiedCase],
    columns_for_export: list[CSVColumn],
    equality_body_csv: bool = False,
) -> Generator[str, None, None]:
    """
    Generate a series of strings containing the content for a CSV streaming response
    """

    class DummyFile:
        def write(self, value_to_write):
            return value_to_write

    writer: Any = csv.writer(DummyFile())
    column_row: list[str] = [column.column_header for column in columns_for_export]

    output: str = writer.writerow(column_row)

    for counter, case in enumerate(cases):
        if equality_body_csv is True:
            case_columns: list[EqualityBodyCSVColumn] = populate_equality_body_columns(
                simplified_case=case
            )
        else:
            case_columns: list[CSVColumn] = populate_csv_columns(
                simplified_case=case, column_definitions=columns_for_export
            )
        row = [column.formatted_data for column in case_columns]
        output += writer.writerow(row)
        if counter % DOWNLOAD_CASES_CHUNK_SIZE == 0:
            yield output
            output = ""
    if output:
        yield output


def download_equality_body_cases(
    cases: QuerySet[SimplifiedCase],
    filename: str = "enforcement_body_cases.csv",
) -> StreamingHttpResponse:
    """Given a Case queryset, download the data in csv format for equality body"""
    response = StreamingHttpResponse(
        csv_output_generator(
            cases=cases,
            columns_for_export=EQUALITY_BODY_COLUMNS_FOR_EXPORT,
            equality_body_csv=True,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def download_simplified_cases(
    simplified_cases: QuerySet[SimplifiedCase], filename: str = "cases.csv"
) -> StreamingHttpResponse:
    """Given a Case queryset, download the data in csv format"""

    response = StreamingHttpResponse(
        csv_output_generator(
            cases=simplified_cases, columns_for_export=CASE_COLUMNS_FOR_EXPORT
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def download_feedback_survey_cases(
    cases: QuerySet[SimplifiedCase], filename: str = "feedback_survey_cases.csv"
) -> StreamingHttpResponse:
    """Given a Case queryset, download the feedback survey data in csv format"""
    response = StreamingHttpResponse(
        csv_output_generator(
            cases=cases, columns_for_export=FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response
