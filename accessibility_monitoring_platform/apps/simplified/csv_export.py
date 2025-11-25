"""Utility functions for CSV exports"""

from ..audits.models import Audit
from ..common.csv_export import CSVColumn, EqualityBodyCSVColumn
from ..reports.models import Report
from ..simplified.models import CaseCompliance
from ..simplified.models import Contact as SimplifiedContact
from ..simplified.models import SimplifiedCase

SIMPLIFIED_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = [
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
        source_attr="case_identifier",
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
        source_attr="previous_case_identifier",
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
SIMPLIFIED_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = [
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
]
SIMPLIFIED_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT: list[
    EqualityBodyCSVColumn
] = [
    EqualityBodyCSVColumn(
        column_header="Contact details",
        source_class=SimplifiedCase,
        source_attr="equality_body_export_contact_details",
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
SIMPLIFIED_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT: list[
    EqualityBodyCSVColumn
] = [
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
SIMPLIFIED_EQUALITY_BODY_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = (
    SIMPLIFIED_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT
    + SIMPLIFIED_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT
    + SIMPLIFIED_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT
    + SIMPLIFIED_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT
)

SIMPLIFIED_CASE_COLUMNS_FOR_EXPORT: list[CSVColumn] = [
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
        column_header="Equality body has officially closed the case?",
        source_class=SimplifiedCase,
        source_attr="enforcement_body_closed_case",
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
    CSVColumn(
        column_header="Contact email",
        source_class=SimplifiedContact,
        source_attr="email",
    ),
]

SIMPLIFIED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT: list[CSVColumn] = [
    CSVColumn(
        column_header="Case no.", source_class=SimplifiedCase, source_attr="case_number"
    ),
    CSVColumn(
        column_header="Website name",
        source_class=SimplifiedCase,
        source_attr="website_name",
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
    CSVColumn(
        column_header="Contact email",
        source_class=SimplifiedContact,
        source_attr="email",
    ),
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
    CSVColumn(
        column_header="Compliance decision email sent to",
        source_class=SimplifiedCase,
        source_attr="compliance_decision_sent_to_email",
    ),
]
