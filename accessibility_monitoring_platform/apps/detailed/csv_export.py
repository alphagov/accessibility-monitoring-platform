"""Utility functions for CSV exports"""

from ..common.csv_export import CSVColumn, EqualityBodyCSVColumn
from ..detailed.models import Contact as DetailedContact
from ..detailed.models import DetailedCase

DETAILED_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = [
    EqualityBodyCSVColumn(
        column_header="Equality body",
        source_class=DetailedCase,
        source_attr="enforcement_body",
        required=True,
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-case-metadata",
        edit_url_anchor="id_enforcement_body-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Test type",
        source_class=DetailedCase,
        source_attr="test_type",
        required=True,
        edit_url_class=DetailedCase,
        edit_url_name=None,
    ),
    EqualityBodyCSVColumn(
        column_header="Case number",
        source_class=DetailedCase,
        source_attr="case_identifier",
        required=True,
        edit_url_class=DetailedCase,
        edit_url_name=None,
    ),
    EqualityBodyCSVColumn(
        column_header="Organisation",
        source_class=DetailedCase,
        source_attr="organisation_name",
        required=True,
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-case-metadata",
        edit_url_anchor="id_organisation_name-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Website URL",
        source_class=DetailedCase,
        source_attr="home_page_url",
        required=True,
        data_type="url",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-case-metadata",
        edit_url_anchor="id_home_page_url-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Parent organisation name",
        source_class=DetailedCase,
        source_attr="parental_organisation_name",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-case-metadata",
        edit_url_anchor="id_parental_organisation_name-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Sub-category",
        source_class=DetailedCase,
        source_attr="subcategory",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-case-metadata",
        edit_url_anchor="id_subcategory-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Website name",
        source_class=DetailedCase,
        source_attr="website_name",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-case-metadata",
        edit_url_anchor="id_website_name-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Previous Case Number",
        source_class=DetailedCase,
        source_attr="previous_case_identifier",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-case-metadata",
        edit_url_anchor="id_previous_case_url-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Is it a complaint?",
        source_class=DetailedCase,
        source_attr="is_complaint",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-case-metadata",
        edit_url_anchor="id_is_complaint-label",
    ),
]
DETAILED_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = [
    EqualityBodyCSVColumn(
        column_header="Published report",
        source_class=DetailedCase,
        source_attr="equality_body_report_url",
        required=True,
        data_type="url",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-final-report",
        edit_url_anchor="id_equality_body_report_url-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Enforcement recommendation",
        source_class=DetailedCase,
        source_attr="recommendation_for_enforcement",
        required=True,
        default_data="Not selected",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-case-recommendation",
        edit_url_anchor="id_recommendation_for_enforcement-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Enforcement recommendation notes including exemptions",
        source_class=DetailedCase,
        source_attr="recommendation_info",
        required=True,
        data_type="markdown",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-case-recommendation",
        edit_url_anchor="id_recommendation_info-label",
    ),
]
DETAILED_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT: list[
    EqualityBodyCSVColumn
] = [
    EqualityBodyCSVColumn(
        column_header="Contact details",
        source_class=DetailedCase,
        source_attr="equality_body_export_contact_details",
        data_type="pre",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:manage-contact-details",
        edit_url_label="Go to contact details",
    ),
    EqualityBodyCSVColumn(
        column_header="Organisation responded to report?",
        source_class=DetailedCase,
        source_attr="report_acknowledged_yes_no",
        ui_suffix=" (derived from report acknowledged date)",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-report-acknowledged",
        edit_url_anchor="id_report_acknowledged_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Report sent on",
        source_class=DetailedCase,
        source_attr="report_sent_date",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-report-sent",
        edit_url_anchor="id_report_sent_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Report acknowledged",
        source_class=DetailedCase,
        source_attr="report_acknowledged_date",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-report-acknowledged",
        edit_url_anchor="id_report_acknowledged_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="12-week deadline",
        source_class=DetailedCase,
        source_attr="twelve_week_deadline_date",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-12-week-deadline",
        edit_url_anchor="id_twelve_week_deadline_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Retest date",
        source_class=DetailedCase,
        source_attr="retest_start_date",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-retest-result",
        edit_url_anchor="id_retest_start_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Date when compliance decision email sent to public sector body",
        source_class=DetailedCase,
        source_attr="recommendation_decision_sent_date",
        required=True,
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-case-recommendation",
        edit_url_anchor="id_recommendation_decision_sent_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Compliance decision email sent to",
        source_class=DetailedCase,
        source_attr="recommendation_decision_sent_to",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-case-recommendation",
        edit_url_anchor="id_recommendation_decision_sent_to-label",
    ),
]
DETAILED_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = [
    EqualityBodyCSVColumn(
        column_header="Total number of accessibility issues",
        source_class=DetailedCase,
        source_attr="initial_total_number_of_issues",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-initial-testing-outcome",
        edit_url_anchor="id_initial_total_number_of_issues-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Number of issues fixed",
        source_class=DetailedCase,
        source_attr="number_of_issues_fixed",
        ui_suffix=" (derived from initial and unfixed numbers of issues)",
        edit_url_class=DetailedCase,
        edit_url_name=None,
    ),
    EqualityBodyCSVColumn(
        column_header="Number of issues unfixed",
        source_class=DetailedCase,
        source_attr="retest_total_number_of_issues",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-retest-result",
        edit_url_anchor="id_retest_total_number_of_issues-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Issues fixed as a percentage",
        source_class=DetailedCase,
        source_attr="percentage_of_issues_fixed",
        ui_suffix="% (Derived from retest results)",
        edit_url_class=DetailedCase,
        edit_url_name=None,
    ),
    EqualityBodyCSVColumn(
        column_header="Was an accessibility statement found during the 12-week assessment",
        source_class=DetailedCase,
        source_attr="equality_body_export_statement_found_at_retest",
        ui_suffix=" (Derived from retest statement compliance decision)",
        edit_url_class=DetailedCase,
        edit_url_name=None,
    ),
    EqualityBodyCSVColumn(
        column_header="Retest Accessibility Statement Decision",
        source_class=DetailedCase,
        source_attr="retest_statement_compliance_state",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-retest-compliance-decisions",
        edit_url_anchor="id_retest_statement_compliance_state-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Retest disproportionate burden claimed?",
        source_class=DetailedCase,
        source_attr="retest_disproportionate_burden_claim",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-retest-compliance-decisions",
        edit_url_anchor="id_retest_disproportionate_burden_claim-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Retest disproportionate burden details",
        source_class=DetailedCase,
        source_attr="retest_disproportionate_burden_information",
        data_type="markdown",
        edit_url_class=DetailedCase,
        edit_url_name="detailed:edit-retest-compliance-decisions",
        edit_url_anchor="id_retest_disproportionate_burden_information-label",
    ),
]
DETAILED_EQUALITY_BODY_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = (
    DETAILED_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT
    + DETAILED_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT
    + DETAILED_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT
    + DETAILED_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT
)

DETAILED_CASE_COLUMNS_FOR_EXPORT: list[CSVColumn] = [
    # General
    CSVColumn(
        column_header="Case no.", source_class=DetailedCase, source_attr="case_number"
    ),
    CSVColumn(
        column_header="Version", source_class=DetailedCase, source_attr="version"
    ),
    CSVColumn(
        column_header="Created by",
        source_class=DetailedCase,
        source_attr="created_by",
    ),
    CSVColumn(
        column_header="Date created", source_class=DetailedCase, source_attr="created"
    ),
    CSVColumn(column_header="Status", source_class=DetailedCase, source_attr="status"),
    CSVColumn(
        column_header="Domain name", source_class=DetailedCase, source_attr="domain"
    ),
    CSVColumn(
        column_header="Type of test",
        source_class=DetailedCase,
        source_attr="test_type",
    ),
    # Case details - Case metadata
    CSVColumn(
        column_header="Full URL",
        source_class=DetailedCase,
        source_attr="home_page_url",
    ),
    CSVColumn(
        column_header="Organisation name",
        source_class=DetailedCase,
        source_attr="organisation_name",
    ),
    CSVColumn(
        column_header="Parent organisation name",
        source_class=DetailedCase,
        source_attr="parental_organisation_name",
    ),
    CSVColumn(
        column_header="Website name",
        source_class=DetailedCase,
        source_attr="website_name",
    ),
    CSVColumn(column_header="Sector", source_class=DetailedCase, source_attr="sector"),
    CSVColumn(
        column_header="Sub-category",
        source_class=DetailedCase,
        source_attr="subcategory",
    ),
    CSVColumn(
        column_header="Which equalities body will check the case?",
        source_class=DetailedCase,
        source_attr="enforcement_body",
    ),
    CSVColumn(
        column_header="Type",
        source_class=DetailedCase,
        source_attr="service_type",
    ),
    CSVColumn(
        column_header="Public sector body location",
        source_class=DetailedCase,
        source_attr="psb_location",
    ),
    CSVColumn(
        column_header="URL to previous case",
        source_class=DetailedCase,
        source_attr="previous_case_url",
    ),
    CSVColumn(
        column_header="Complaint?",
        source_class=DetailedCase,
        source_attr="is_complaint",
    ),
    CSVColumn(
        column_header="Link to case folder",
        source_class=DetailedCase,
        source_attr="case_folder_url",
    ),
    CSVColumn(
        column_header="Feedback survey sent?",
        source_class=DetailedCase,
        source_attr="is_feedback_requested",
    ),
    CSVColumn(
        column_header="Case details case metadata page complete",
        source_class=DetailedCase,
        source_attr="case_metadata_complete_date",
    ),
    # Initial contact - contact details
    CSVColumn(
        column_header="Contact name", source_class=DetailedContact, source_attr="name"
    ),
    CSVColumn(
        column_header="Contact job title",
        source_class=DetailedContact,
        source_attr="job_title",
    ),
    CSVColumn(
        column_header="Contact details",
        source_class=DetailedContact,
        source_attr="contact_details",
    ),
    # Initial contact - Information request
    CSVColumn(
        column_header="Information request process started",
        source_class=DetailedCase,
        source_attr="contact_information_request_start_date",
    ),
    CSVColumn(
        column_header="Information received",
        source_class=DetailedCase,
        source_attr="contact_information_request_end_date",
    ),
    CSVColumn(
        column_header="Contact information request page complete",
        source_class=DetailedCase,
        source_attr="contact_information_request_complete_date",
    ),
    # Initial test - Testing
    CSVColumn(
        column_header="Auditor",
        source_class=DetailedCase,
        source_attr="auditor",
    ),
    CSVColumn(
        column_header="Test start date",
        source_class=DetailedCase,
        source_attr="initial_test_start_date",
    ),
    CSVColumn(
        column_header="Initial test testing page complete",
        source_class=DetailedCase,
        source_attr="initial_testing_details_complete_date",
    ),
    # Initial test - Testing outcome
    CSVColumn(
        column_header="Test end date",
        source_class=DetailedCase,
        source_attr="initial_test_end_date",
    ),
    CSVColumn(
        column_header="Number of pages tested",
        source_class=DetailedCase,
        source_attr="initial_total_number_of_pages",
    ),
    CSVColumn(
        column_header="Number of issues found",
        source_class=DetailedCase,
        source_attr="initial_total_number_of_issues",
    ),
    CSVColumn(
        column_header="Initial website compliance decision",
        source_class=DetailedCase,
        source_attr="initial_website_compliance_state",
    ),
    CSVColumn(
        column_header="Initial statement compliance decision",
        source_class=DetailedCase,
        source_attr="initial_statement_compliance_state",
    ),
    CSVColumn(
        column_header="Initial disproportionate burden claim",
        source_class=DetailedCase,
        source_attr="initial_disproportionate_burden_claim",
    ),
    CSVColumn(
        column_header="Initial test testing outcome page complete",
        source_class=DetailedCase,
        source_attr="initial_testing_outcome_complete_date",
    ),
    # Report - Report ready for QA
    CSVColumn(
        column_header="Report ready for QA process?",
        source_class=DetailedCase,
        source_attr="report_ready_for_qa",
    ),
    CSVColumn(
        column_header="Report report ready for QA page complete",
        source_class=DetailedCase,
        source_attr="report_ready_for_qa_complete_date",
    ),
    # Report - QA auditor
    CSVColumn(
        column_header="QA auditor",
        source_class=DetailedCase,
        source_attr="reviewer",
    ),
    CSVColumn(
        column_header="Report QA auditor page complete",
        source_class=DetailedCase,
        source_attr="qa_auditor_complete_date",
    ),
    # Report - QA approval
    CSVColumn(
        column_header="Report approved?",
        source_class=DetailedCase,
        source_attr="report_approved_status",
    ),
    CSVColumn(
        column_header="Report QA approval page complete",
        source_class=DetailedCase,
        source_attr="qa_approval_complete_date",
    ),
    # Report - Final report
    CSVColumn(
        column_header="Link to equality body PDF report",
        source_class=DetailedCase,
        source_attr="equality_body_report_url",
    ),
    CSVColumn(
        column_header="Report final report page complete",
        source_class=DetailedCase,
        source_attr="final_report_complete_date",
    ),
    # Correspondence - Report sent
    CSVColumn(
        column_header="Report sent on",
        source_class=DetailedCase,
        source_attr="report_sent_date",
    ),
    CSVColumn(
        column_header="Correspondence report sent page complete",
        source_class=DetailedCase,
        source_attr="report_sent_complete_date",
    ),
    # Correspondence - 12-week deadline
    CSVColumn(
        column_header="12-week deadline",
        source_class=DetailedCase,
        source_attr="twelve_week_deadline_date",
    ),
    CSVColumn(
        column_header="Correspondence 12-week deadline page complete",
        source_class=DetailedCase,
        source_attr="twelve_week_deadline_complete_date",
    ),
    # Correspondence - Report acknowledged
    CSVColumn(
        column_header="Report acknowledged on",
        source_class=DetailedCase,
        source_attr="report_acknowledged_date",
    ),
    CSVColumn(
        column_header="Correspondence report acknowledged page complete",
        source_class=DetailedCase,
        source_attr="report_acknowledged_complete_date",
    ),
    # Correspondence - 12-week update request
    CSVColumn(
        column_header="12-week update requested",
        source_class=DetailedCase,
        source_attr="twelve_week_update_date",
    ),
    CSVColumn(
        column_header="Correspondence 12-week update request page complete",
        source_class=DetailedCase,
        source_attr="twelve_week_update_complete_date",
    ),
    # Correspondence - 12-week update received
    CSVColumn(
        column_header="12-week update received",
        source_class=DetailedCase,
        source_attr="twelve_week_received_date",
    ),
    CSVColumn(
        column_header="Correspondence 12-week update received page complete",
        source_class=DetailedCase,
        source_attr="twelve_week_received_complete_date",
    ),
    # Reviewing changes - Retest result
    CSVColumn(
        column_header="Latest retest date",
        source_class=DetailedCase,
        source_attr="retest_start_date",
    ),
    CSVColumn(
        column_header="Total number of remaining issues",
        source_class=DetailedCase,
        source_attr="retest_total_number_of_issues",
    ),
    CSVColumn(
        column_header="Reviewing changes retest result page complete",
        source_class=DetailedCase,
        source_attr="retest_result_complete_date",
    ),
    # Reviewing changes - Compliance decisions
    CSVColumn(
        column_header="Retest website compliance decision",
        source_class=DetailedCase,
        source_attr="retest_website_compliance_state",
    ),
    CSVColumn(
        column_header="Retest website compliance decision information",
        source_class=DetailedCase,
        source_attr="retest_website_compliance_information",
    ),
    CSVColumn(
        column_header="Retest statement compliance decision",
        source_class=DetailedCase,
        source_attr="retest_statement_compliance_state",
    ),
    CSVColumn(
        column_header="Retest statement compliance decision information",
        source_class=DetailedCase,
        source_attr="retest_statement_compliance_information",
    ),
    CSVColumn(
        column_header="Retest disproportionate burden claim",
        source_class=DetailedCase,
        source_attr="retest_disproportionate_burden_claim",
    ),
    CSVColumn(
        column_header="Retest disproportionate burden information",
        source_class=DetailedCase,
        source_attr="retest_disproportionate_burden_information",
    ),
    CSVColumn(
        column_header="Reviewing changes compliance decisions page complete",
        source_class=DetailedCase,
        source_attr="retest_compliance_decisions_complete_date",
    ),
    # Closing the case - Closing the case
    CSVColumn(
        column_header="Case progress notes",
        source_class=DetailedCase,
        source_attr="psb_progress_info",
    ),
    CSVColumn(
        column_header="Enforcement recommendation",
        source_class=DetailedCase,
        source_attr="recommendation_for_enforcement",
    ),
    CSVColumn(
        column_header="Enforcement recommendation details",
        source_class=DetailedCase,
        source_attr="recommendation_info",
    ),
    CSVColumn(
        column_header="Date decision email sent",
        source_class=DetailedCase,
        source_attr="recommendation_decision_sent_date",
    ),
    CSVColumn(
        column_header="Decision sent to",
        source_class=DetailedCase,
        source_attr="recommendation_decision_sent_to",
    ),
    CSVColumn(
        column_header="Case completed",
        source_class=DetailedCase,
        source_attr="case_close_decision_state",
    ),
    CSVColumn(
        column_header="Case added to stats tab?",
        source_class=DetailedCase,
        source_attr="is_case_added_to_stats",
    ),
    CSVColumn(
        column_header="Closing the case closing the case page complete",
        source_class=DetailedCase,
        source_attr="case_close_complete_date",
    ),
    # Post case - Statement enforcement
    CSVColumn(
        column_header="Public sector body appeal information",
        source_class=DetailedCase,
        source_attr="psb_statement_appeal_information",
    ),
    CSVColumn(
        column_header="Post case statement enforcement page complete",
        source_class=DetailedCase,
        source_attr="statement_enforcement_complete_date",
    ),
    # Post case - Equality body metadata
    CSVColumn(
        column_header="Date sent to equality body",
        source_class=DetailedCase,
        source_attr="enforcement_body_sent_date",
    ),
    CSVColumn(
        column_header="Date equality body started the case",
        source_class=DetailedCase,
        source_attr="enforcement_body_started_date",
    ),
    CSVColumn(
        column_header="Equality body case owner (first name only)",
        source_class=DetailedCase,
        source_attr="enforcement_body_case_owner",
    ),
    CSVColumn(
        column_header="Equality body has officially closed the case?",
        source_class=DetailedCase,
        source_attr="enforcement_body_closed_case_state",
    ),
    CSVColumn(
        column_header="Date equality body completed the case",
        source_class=DetailedCase,
        source_attr="enforcement_body_completed_case_date",
    ),
    CSVColumn(
        column_header="Post case equality body metadata page complete",
        source_class=DetailedCase,
        source_attr="enforcement_body_metadata_complete_date",
    ),
    # Case tools - Unresponsive PSB
    CSVColumn(
        column_header="Do you want to mark the PSB as unresponsive to this case?",
        source_class=DetailedCase,
        source_attr="no_psb_contact",
    ),
    CSVColumn(
        column_header="Public sector body is unresponsive information",
        source_class=DetailedCase,
        source_attr="no_psb_contact_info",
    ),
]
DETAILED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT: list[CSVColumn] = [
    CSVColumn(
        column_header="Case no.", source_class=DetailedCase, source_attr="case_number"
    ),
    CSVColumn(
        column_header="Website name",
        source_class=DetailedCase,
        source_attr="website_name",
    ),
    CSVColumn(
        column_header="Organisation name",
        source_class=DetailedCase,
        source_attr="organisation_name",
    ),
    CSVColumn(
        column_header="Closing the case date",
        source_class=DetailedCase,
        source_attr="recommendation_decision_sent_date",
    ),
    CSVColumn(
        column_header="Enforcement recommendation",
        source_class=DetailedCase,
        source_attr="recommendation_for_enforcement",
    ),
    CSVColumn(
        column_header="Enforcement recommendation notes",
        source_class=DetailedCase,
        source_attr="recommendation_info",
    ),
    CSVColumn(
        column_header="Final statement decision",
        source_class=DetailedCase,
        source_attr="retest_statement_compliance_state",
    ),
    CSVColumn(
        column_header="Contact email",
        source_class=DetailedContact,
        source_attr="contact_details",
    ),
    CSVColumn(
        column_header="Contact notes",
        source_class=DetailedContact,
        source_attr="information",
    ),
    CSVColumn(
        column_header="Feedback survey sent?",
        source_class=DetailedCase,
        source_attr="is_feedback_requested",
    ),
]
