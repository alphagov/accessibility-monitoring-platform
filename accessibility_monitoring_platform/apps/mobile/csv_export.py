"""Utility functions for CSV exports"""

import copy
import csv
from dataclasses import dataclass
from typing import Any, Generator

from django.db.models.query import QuerySet
from django.urls import reverse

from ..cases.csv_export import DOWNLOAD_CASES_CHUNK_SIZE
from ..common.csv_export import CSVColumn, EqualityBodyCSVColumn, format_model_field
from .models import IOS_ANDROID_SEPARATOR, MobileCase, MobileContact


@dataclass
class MobileEqualityBodyCSVColumn:
    """
    Data to use when building export CSV for equality body and to show in UI for
    mobile case
    """

    column_header: str
    source_attr: str
    source_class: MobileCase = MobileCase
    mobile_equality_body_csv_column: bool = True
    ios_edit_url_name: str | None = None
    ios_edit_url_label: str = "Edit iOS"
    ios_edit_url_anchor: str = ""
    ios_edit_url: str | None = None
    android_edit_url_name: str | None = None
    android_edit_url_label: str = "Edit Android"
    android_edit_url_anchor: str = ""
    android_edit_url: str | None = None
    required_data_missing: bool = False
    formatted_data: str = ""
    formatted_ui_data: str = ""
    ui_suffix: str = ""


MOBILE_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = [
    EqualityBodyCSVColumn(
        column_header="Equality body",
        source_class=MobileCase,
        source_attr="enforcement_body",
        required=True,
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-case-metadata",
        edit_url_anchor="id_enforcement_body-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Test type",
        source_class=MobileCase,
        source_attr="test_type",
        required=True,
        edit_url_class=MobileCase,
        edit_url_name=None,
    ),
    EqualityBodyCSVColumn(
        column_header="Case number",
        source_class=MobileCase,
        source_attr="case_identifier",
        required=True,
        edit_url_class=MobileCase,
        edit_url_name=None,
    ),
    EqualityBodyCSVColumn(
        column_header="Organisation",
        source_class=MobileCase,
        source_attr="organisation_name",
        required=True,
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-case-metadata",
        edit_url_anchor="id_organisation_name-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Website URL",
        source_class=MobileCase,
        source_attr="home_page_url",
        required=True,
        data_type="url",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-case-metadata",
        edit_url_anchor="id_home_page_url-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Parent organisation name",
        source_class=MobileCase,
        source_attr="parental_organisation_name",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-case-metadata",
        edit_url_anchor="id_parental_organisation_name-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Sub-category",
        source_class=MobileCase,
        source_attr="subcategory",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-case-metadata",
        edit_url_anchor="id_subcategory-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Website or app name",
        source_class=MobileCase,
        source_attr="app_name",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-case-metadata",
        edit_url_anchor="id_app_name-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Previous Case Number",
        source_class=MobileCase,
        source_attr="previous_case_identifier",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-case-metadata",
        edit_url_anchor="id_previous_case_url-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Is it a complaint?",
        source_class=MobileCase,
        source_attr="is_complaint",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-case-metadata",
        edit_url_anchor="id_is_complaint-label",
    ),
]
MOBILE_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = [
    MobileEqualityBodyCSVColumn(
        column_header="Published report",
        source_attr="equality_body_report_urls",
        ios_edit_url_name="mobile:edit-final-report",
        ios_edit_url_anchor="id_equality_body_report_url_ios-label",
        android_edit_url_name="mobile:edit-final-report",
        android_edit_url_anchor="id_equality_body_report_url_android-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Enforcement recommendation",
        source_class=MobileCase,
        source_attr="recommendation_for_enforcement",
        required=True,
        default_data="Not selected",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-case-recommendation",
        edit_url_anchor="id_recommendation_for_enforcement-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Enforcement recommendation notes including exemptions",
        source_class=MobileCase,
        source_attr="recommendation_info",
        required=True,
        data_type="markdown",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-case-recommendation",
        edit_url_anchor="id_recommendation_info-label",
    ),
]
MOBILE_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = [
    EqualityBodyCSVColumn(
        column_header="Contact details",
        source_class=MobileCase,
        source_attr="equality_body_export_contact_details",
        data_type="pre",
        edit_url_class=MobileCase,
        edit_url_name="mobile:manage-contact-details",
        edit_url_label="Go to contact details",
    ),
    EqualityBodyCSVColumn(
        column_header="Organisation responded to report?",
        source_class=MobileCase,
        source_attr="report_acknowledged_yes_no",
        ui_suffix=" (derived from report acknowledged date)",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-report-acknowledged",
        edit_url_anchor="id_report_acknowledged_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Report sent on",
        source_class=MobileCase,
        source_attr="report_sent_date",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-report-sent",
        edit_url_anchor="id_report_sent_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Report acknowledged",
        source_class=MobileCase,
        source_attr="report_acknowledged_date",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-report-acknowledged",
        edit_url_anchor="id_report_acknowledged_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="12-week deadline",
        source_class=MobileCase,
        source_attr="twelve_week_deadline_date",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-12-week-deadline",
        edit_url_anchor="id_twelve_week_deadline_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Retest date",
        source_class=MobileCase,
        source_attr="retest_start_date",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-retest-ios-result",
        edit_url_anchor="id_retest_start_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Date when compliance decision email sent to public sector body",
        source_class=MobileCase,
        source_attr="recommendation_decision_sent_date",
        required=True,
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-case-recommendation",
        edit_url_anchor="id_recommendation_decision_sent_date-label",
    ),
    EqualityBodyCSVColumn(
        column_header="Compliance decision email sent to",
        source_class=MobileCase,
        source_attr="recommendation_decision_sent_to",
        edit_url_class=MobileCase,
        edit_url_name="mobile:edit-case-recommendation",
        edit_url_anchor="id_recommendation_decision_sent_to-label",
    ),
]
MOBILE_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = [
    MobileEqualityBodyCSVColumn(
        column_header="Total number of accessibility issues",
        source_attr="initial_total_number_of_issues",
        ios_edit_url_name="mobile:edit-initial-test-ios-outcome",
        ios_edit_url_anchor="id_initial_ios_total_number_of_issues-label",
        android_edit_url_name="mobile:edit-initial-test-android-outcome",
        android_edit_url_anchor="id_initial_android_total_number_of_issues-label",
    ),
    MobileEqualityBodyCSVColumn(
        column_header="Number of issues fixed",
        source_attr="number_of_issues_fixed",
        ui_suffix="(Total number of accessibility issues - Number of issues unfixed)",
    ),
    MobileEqualityBodyCSVColumn(
        column_header="Number of issues unfixed",
        source_attr="retest_total_number_of_issues_unfixed",
        ios_edit_url_name="mobile:edit-retest-ios-result",
        ios_edit_url_anchor="id_retest_ios_total_number_of_issues-label",
        android_edit_url_name="mobile:edit-retest-android-result",
        android_edit_url_anchor="id_retest_android_total_number_of_issues-label",
    ),
    MobileEqualityBodyCSVColumn(
        column_header="Issues fixed as a percentage",
        source_attr="percentage_of_issues_fixed",
        ui_suffix="(Number of issues fixed / Total number of accessibility issues)",
    ),
    MobileEqualityBodyCSVColumn(
        column_header="Was an accessibility statement found during the 12-week assessment",
        source_attr="equality_body_export_statement_found_at_retest",
        ui_suffix="<br>(Derived from retest statement compliance decisions)",
        ios_edit_url_name="mobile:edit-retest-ios-compliance-decisions",
        ios_edit_url_anchor="id_retest_ios_statement_compliance_state-label",
        android_edit_url_name="mobile:edit-retest-android-compliance-decisions",
        android_edit_url_anchor="id_retest_android_statement_compliance_state-label",
    ),
    MobileEqualityBodyCSVColumn(
        column_header="Retest Accessibility Statement Decision",
        source_attr="retest_statement_compliance_state",
        ios_edit_url_name="mobile:edit-retest-ios-compliance-decisions",
        ios_edit_url_anchor="id_retest_ios_statement_compliance_state-label",
        android_edit_url_name="mobile:edit-retest-android-compliance-decisions",
        android_edit_url_anchor="id_retest_android_statement_compliance_state-label",
    ),
    MobileEqualityBodyCSVColumn(
        column_header="Retest disproportionate burden claimed?",
        source_attr="retest_disproportionate_burden_claim",
        ios_edit_url_name="mobile:edit-retest-ios-compliance-decisions",
        ios_edit_url_anchor="id_retest_ios_disproportionate_burden_claim-label",
        android_edit_url_name="mobile:edit-retest-android-compliance-decisions",
        android_edit_url_anchor="id_retest_android_disproportionate_burden_claim-label",
    ),
    MobileEqualityBodyCSVColumn(
        column_header="Retest disproportionate burden details",
        source_attr="retest_disproportionate_burden_information",
        ios_edit_url_name="mobile:edit-retest-ios-compliance-decisions",
        ios_edit_url_anchor="id_retest_ios_disproportionate_burden_information-label",
        android_edit_url_name="mobile:edit-retest-android-compliance-decisions",
        android_edit_url_anchor="id_retest_android_disproportionate_burden_information-label",
    ),
]
MOBILE_EQUALITY_BODY_COLUMNS_FOR_EXPORT: list[EqualityBodyCSVColumn] = (
    MOBILE_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT
    + MOBILE_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT
    + MOBILE_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT
    + MOBILE_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT
)

MOBILE_CASE_COLUMNS_FOR_EXPORT: list[CSVColumn] = [
    # General
    CSVColumn(
        column_header="Case no.", source_class=MobileCase, source_attr="case_number"
    ),
    CSVColumn(column_header="Version", source_class=MobileCase, source_attr="version"),
    CSVColumn(
        column_header="Created by",
        source_class=MobileCase,
        source_attr="created_by",
    ),
    CSVColumn(
        column_header="Date created", source_class=MobileCase, source_attr="created"
    ),
    CSVColumn(column_header="Status", source_class=MobileCase, source_attr="status"),
    CSVColumn(
        column_header="Domain name", source_class=MobileCase, source_attr="domain"
    ),
    CSVColumn(
        column_header="Type of test",
        source_class=MobileCase,
        source_attr="test_type",
    ),
    # Case details - Case metadata
    CSVColumn(
        column_header="Full URL · Included in export",
        source_class=MobileCase,
        source_attr="home_page_url",
    ),
    CSVColumn(
        column_header="Organisation name · Included in export",
        source_class=MobileCase,
        source_attr="organisation_name",
    ),
    CSVColumn(
        column_header="Parent organisation name · Included in export",
        source_class=MobileCase,
        source_attr="parental_organisation_name",
    ),
    CSVColumn(
        column_header="App name",
        source_class=MobileCase,
        source_attr="app_name",
    ),
    CSVColumn(
        column_header="Android app URL",
        source_class=MobileCase,
        source_attr="android_app_url",
    ),
    CSVColumn(
        column_header="iOS app URL",
        source_class=MobileCase,
        source_attr="ios_app_app_url",
    ),
    CSVColumn(column_header="Sector", source_class=MobileCase, source_attr="sector"),
    CSVColumn(
        column_header="Sub-category · Included in export",
        source_class=MobileCase,
        source_attr="subcategory",
    ),
    CSVColumn(
        column_header="Which equalities body will check the case? · Included in export",
        source_class=MobileCase,
        source_attr="enforcement_body",
    ),
    CSVColumn(
        column_header="Public sector body location",
        source_class=MobileCase,
        source_attr="psb_location",
    ),
    CSVColumn(
        column_header="URL to previous case · Included in export",
        source_class=MobileCase,
        source_attr="previous_case_url",
    ),
    CSVColumn(
        column_header="Complaint? · Included in export",
        source_class=MobileCase,
        source_attr="is_complaint",
    ),
    CSVColumn(
        column_header="Link to case folder",
        source_class=MobileCase,
        source_attr="case_folder_url",
    ),
    CSVColumn(
        column_header="Feedback survey sent?",
        source_class=MobileCase,
        source_attr="is_feedback_requested",
    ),
    CSVColumn(
        column_header="Case details case metadata page complete",
        source_class=MobileCase,
        source_attr="case_metadata_complete_date",
    ),
    # Initial contact - contact details
    CSVColumn(
        column_header="Contact name", source_class=MobileContact, source_attr="name"
    ),
    CSVColumn(
        column_header="Contact job title",
        source_class=MobileContact,
        source_attr="job_title",
    ),
    CSVColumn(
        column_header="Contact details",
        source_class=MobileContact,
        source_attr="contact_details",
    ),
    # Initial contact - Information request
    CSVColumn(
        column_header="Information request process started",
        source_class=MobileCase,
        source_attr="contact_information_request_start_date",
    ),
    CSVColumn(
        column_header="Information received",
        source_class=MobileCase,
        source_attr="contact_information_request_end_date",
    ),
    CSVColumn(
        column_header="Contact information request page complete",
        source_class=MobileCase,
        source_attr="contact_information_request_complete_date",
    ),
    # Initial test - Auditor
    CSVColumn(
        column_header="Auditor",
        source_class=MobileCase,
        source_attr="auditor",
    ),
    CSVColumn(
        column_header="Initial test auditor page complete",
        source_class=MobileCase,
        source_attr="initial_auditor_complete_date",
    ),
    # Initial test - iOS details
    CSVColumn(
        column_header="iOS test start date",
        source_class=MobileCase,
        source_attr="initial_ios_test_start_date",
    ),
    CSVColumn(
        column_header="iOS initial test testing page complete",
        source_class=MobileCase,
        source_attr="initial_ios_details_complete_date",
    ),
    # Initial test - iOS outcome
    CSVColumn(
        column_header="iOS test end date",
        source_class=MobileCase,
        source_attr="initial_ios_test_end_date",
    ),
    CSVColumn(
        column_header="iOS number of screens tested",
        source_class=MobileCase,
        source_attr="initial_ios_total_number_of_screens",
    ),
    CSVColumn(
        column_header="iOS number of issues found · Included in export",
        source_class=MobileCase,
        source_attr="initial_ios_total_number_of_issues",
    ),
    CSVColumn(
        column_header="iOS initial website compliance decision",
        source_class=MobileCase,
        source_attr="initial_ios_app_compliance_state",
    ),
    CSVColumn(
        column_header="iOS initial statement compliance decision",
        source_class=MobileCase,
        source_attr="initial_ios_statement_compliance_state",
    ),
    CSVColumn(
        column_header="iOS initial disproportionate burden claim",
        source_class=MobileCase,
        source_attr="initial_ios_disproportionate_burden_claim",
    ),
    CSVColumn(
        column_header="iOS initial test testing outcome page complete",
        source_class=MobileCase,
        source_attr="initial_ios_testing_outcome_complete_date",
    ),
    # Initial test - Android details
    CSVColumn(
        column_header="Android test start date",
        source_class=MobileCase,
        source_attr="initial_android_test_start_date",
    ),
    CSVColumn(
        column_header="Android initial test testing page complete",
        source_class=MobileCase,
        source_attr="initial_android_details_complete_date",
    ),
    # Initial test - Android outcome
    CSVColumn(
        column_header="Android test end date",
        source_class=MobileCase,
        source_attr="initial_android_test_end_date",
    ),
    CSVColumn(
        column_header="Android number of screens tested",
        source_class=MobileCase,
        source_attr="initial_android_total_number_of_screens",
    ),
    CSVColumn(
        column_header="Android number of issues found · Included in export",
        source_class=MobileCase,
        source_attr="initial_android_total_number_of_issues",
    ),
    CSVColumn(
        column_header="Android initial website compliance decision",
        source_class=MobileCase,
        source_attr="initial_android_app_compliance_state",
    ),
    CSVColumn(
        column_header="Android initial statement compliance decision",
        source_class=MobileCase,
        source_attr="initial_android_statement_compliance_state",
    ),
    CSVColumn(
        column_header="Android initial disproportionate burden claim",
        source_class=MobileCase,
        source_attr="initial_android_disproportionate_burden_claim",
    ),
    CSVColumn(
        column_header="Android initial test testing outcome page complete",
        source_class=MobileCase,
        source_attr="initial_android_testing_outcome_complete_date",
    ),
    # Report - Report ready for QA
    CSVColumn(
        column_header="Report ready for QA process?",
        source_class=MobileCase,
        source_attr="report_ready_for_qa",
    ),
    CSVColumn(
        column_header="Report report ready for QA page complete",
        source_class=MobileCase,
        source_attr="report_ready_for_qa_complete_date",
    ),
    # Report - QA auditor
    CSVColumn(
        column_header="QA auditor",
        source_class=MobileCase,
        source_attr="reviewer",
    ),
    CSVColumn(
        column_header="Report QA auditor page complete",
        source_class=MobileCase,
        source_attr="qa_auditor_complete_date",
    ),
    # Report - QA approval
    CSVColumn(
        column_header="Report approved?",
        source_class=MobileCase,
        source_attr="report_approved_status",
    ),
    CSVColumn(
        column_header="Report QA approval page complete",
        source_class=MobileCase,
        source_attr="qa_approval_complete_date",
    ),
    # Report - Final report
    CSVColumn(
        column_header="Link to equality body PDF report for iOS · Included in export",
        source_class=MobileCase,
        source_attr="equality_body_report_url_ios",
    ),
    CSVColumn(
        column_header="Link to equality body PDF report for Android · Included in export",
        source_class=MobileCase,
        source_attr="equality_body_report_url_android",
    ),
    CSVColumn(
        column_header="Report final report page complete",
        source_class=MobileCase,
        source_attr="final_report_complete_date",
    ),
    # Correspondence - Report sent
    CSVColumn(
        column_header="Report sent on · Included in export",
        source_class=MobileCase,
        source_attr="report_sent_date",
    ),
    CSVColumn(
        column_header="Correspondence report sent page complete",
        source_class=MobileCase,
        source_attr="report_sent_complete_date",
    ),
    # Correspondence - 12-week deadline
    CSVColumn(
        column_header="12-week deadline · Included in export",
        source_class=MobileCase,
        source_attr="twelve_week_deadline_date",
    ),
    CSVColumn(
        column_header="Correspondence 12-week deadline page complete",
        source_class=MobileCase,
        source_attr="twelve_week_deadline_complete_date",
    ),
    # Correspondence - Report acknowledged
    CSVColumn(
        column_header="Report acknowledged on · Included in export",
        source_class=MobileCase,
        source_attr="report_acknowledged_date",
    ),
    CSVColumn(
        column_header="Correspondence report acknowledged page complete",
        source_class=MobileCase,
        source_attr="report_acknowledged_complete_date",
    ),
    # Correspondence - 12-week update request
    CSVColumn(
        column_header="12-week update requested",
        source_class=MobileCase,
        source_attr="twelve_week_update_date",
    ),
    CSVColumn(
        column_header="Correspondence 12-week update request page complete",
        source_class=MobileCase,
        source_attr="twelve_week_update_complete_date",
    ),
    # Correspondence - 12-week update received
    CSVColumn(
        column_header="12-week update received",
        source_class=MobileCase,
        source_attr="twelve_week_received_date",
    ),
    CSVColumn(
        column_header="Correspondence 12-week update received page complete",
        source_class=MobileCase,
        source_attr="twelve_week_received_complete_date",
    ),
    # Reviewing changes - Retest result
    CSVColumn(
        column_header="Latest retest date · Included in export",
        source_class=MobileCase,
        source_attr="retest_start_date",
    ),
    CSVColumn(
        column_header="Total number of remaining issues · Included in export",
        source_class=MobileCase,
        source_attr="retest_total_number_of_issues",
    ),
    CSVColumn(
        column_header="Reviewing changes retest result page complete",
        source_class=MobileCase,
        source_attr="retest_result_complete_date",
    ),
    # Reviewing changes - Compliance decisions
    CSVColumn(
        column_header="Retest website compliance decision · Included in export",
        source_class=MobileCase,
        source_attr="retest_website_compliance_state",
    ),
    CSVColumn(
        column_header="Retest website compliance decision information",
        source_class=MobileCase,
        source_attr="retest_website_compliance_information",
    ),
    CSVColumn(
        column_header="Retest statement compliance decision · Included in export",
        source_class=MobileCase,
        source_attr="retest_statement_compliance_state",
    ),
    CSVColumn(
        column_header="Retest statement compliance decision information",
        source_class=MobileCase,
        source_attr="retest_statement_compliance_information",
    ),
    CSVColumn(
        column_header="Retest disproportionate burden claim · Included in export",
        source_class=MobileCase,
        source_attr="retest_disproportionate_burden_claim",
    ),
    CSVColumn(
        column_header="Retest disproportionate burden information · Included in export",
        source_class=MobileCase,
        source_attr="retest_disproportionate_burden_information",
    ),
    CSVColumn(
        column_header="Reviewing changes compliance decisions page complete",
        source_class=MobileCase,
        source_attr="retest_compliance_decisions_complete_date",
    ),
    # Closing the case - Closing the case
    CSVColumn(
        column_header="Progress summary and PSB response · Included in export",
        source_class=MobileCase,
        source_attr="psb_progress_info",
    ),
    CSVColumn(
        column_header="Enforcement recommendation · Included in export",
        source_class=MobileCase,
        source_attr="recommendation_for_enforcement",
    ),
    CSVColumn(
        column_header="Enforcement recommendation details · Included in export",
        source_class=MobileCase,
        source_attr="recommendation_info",
    ),
    CSVColumn(
        column_header="Date decision email sent · Included in export",
        source_class=MobileCase,
        source_attr="recommendation_decision_sent_date",
    ),
    CSVColumn(
        column_header="Decision sent to · Included in export",
        source_class=MobileCase,
        source_attr="recommendation_decision_sent_to",
    ),
    CSVColumn(
        column_header="Case completed",
        source_class=MobileCase,
        source_attr="case_close_decision_state",
    ),
    CSVColumn(
        column_header="Case added to stats tab?",
        source_class=MobileCase,
        source_attr="is_case_added_to_stats",
    ),
    CSVColumn(
        column_header="Closing the case closing the case page complete",
        source_class=MobileCase,
        source_attr="case_close_complete_date",
    ),
    # Post case - Statement enforcement
    CSVColumn(
        column_header="Public sector body appeal information",
        source_class=MobileCase,
        source_attr="psb_statement_appeal_information",
    ),
    CSVColumn(
        column_header="Post case statement enforcement page complete",
        source_class=MobileCase,
        source_attr="statement_enforcement_complete_date",
    ),
    # Post case - Equality body metadata
    CSVColumn(
        column_header="Date sent to equality body",
        source_class=MobileCase,
        source_attr="enforcement_body_sent_date",
    ),
    CSVColumn(
        column_header="Date equality body started the case",
        source_class=MobileCase,
        source_attr="enforcement_body_started_date",
    ),
    CSVColumn(
        column_header="Equality body case owner (first name only)",
        source_class=MobileCase,
        source_attr="enforcement_body_case_owner",
    ),
    CSVColumn(
        column_header="Equality body has officially closed the case?",
        source_class=MobileCase,
        source_attr="enforcement_body_closed_case_state",
    ),
    CSVColumn(
        column_header="Date equality body completed the case",
        source_class=MobileCase,
        source_attr="enforcement_body_completed_case_date",
    ),
    CSVColumn(
        column_header="Post case equality body metadata page complete",
        source_class=MobileCase,
        source_attr="enforcement_body_metadata_complete_date",
    ),
    # Case tools - Unresponsive PSB
    CSVColumn(
        column_header="Do you want to mark the PSB as unresponsive to this case?",
        source_class=MobileCase,
        source_attr="no_psb_contact",
    ),
    CSVColumn(
        column_header="Public sector body is unresponsive information",
        source_class=MobileCase,
        source_attr="no_psb_contact_info",
    ),
]
MOBILE_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT: list[CSVColumn] = [
    CSVColumn(
        column_header="Case no.", source_class=MobileCase, source_attr="case_number"
    ),
    CSVColumn(
        column_header="Organisation name",
        source_class=MobileCase,
        source_attr="organisation_name",
    ),
    CSVColumn(
        column_header="Closing the case date",
        source_class=MobileCase,
        source_attr="recommendation_decision_sent_date",
    ),
    CSVColumn(
        column_header="Enforcement recommendation",
        source_class=MobileCase,
        source_attr="recommendation_for_enforcement",
    ),
    CSVColumn(
        column_header="Enforcement recommendation notes",
        source_class=MobileCase,
        source_attr="recommendation_info",
    ),
    CSVColumn(
        column_header="Final statement decision",
        source_class=MobileCase,
        source_attr="retest_ios_statement_compliance_state",
    ),
    CSVColumn(
        column_header="Contact email",
        source_class=MobileContact,
        source_attr="contact_details",
    ),
    CSVColumn(
        column_header="Contact notes",
        source_class=MobileContact,
        source_attr="information",
    ),
    CSVColumn(
        column_header="Feedback survey sent?",
        source_class=MobileCase,
        source_attr="is_feedback_requested",
    ),
]


def populate_mobile_equality_body_columns(
    mobile_case: MobileCase,
    column_definitions: list[
        EqualityBodyCSVColumn | MobileEqualityBodyCSVColumn
    ] = MOBILE_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
) -> list[EqualityBodyCSVColumn]:
    """Collect data for a mobile case to export to the equality body"""

    columns: list[EqualityBodyCSVColumn | MobileEqualityBodyCSVColumn] = copy.deepcopy(
        column_definitions
    )

    for column in columns:
        if isinstance(column, MobileEqualityBodyCSVColumn):
            if column.ios_edit_url_name is not None:
                column.ios_edit_url = reverse(
                    column.ios_edit_url_name, kwargs={"pk": mobile_case.id}
                )
                if column.ios_edit_url_anchor:
                    column.ios_edit_url += f"#{column.ios_edit_url_anchor}"

            if column.android_edit_url_name is not None:
                column.android_edit_url = reverse(
                    column.android_edit_url_name, kwargs={"pk": mobile_case.id}
                )
                if column.android_edit_url_anchor:
                    column.android_edit_url += f"#{column.android_edit_url_anchor}"

            # column.required_data_missing = (
            #     mobile_case.ios_test_included == MobileCase.TestIncluded.YES
            #     and MobileCase.ios_app_url == ""
            # ) or (
            #     mobile_case.android_test_included == MobileCase.TestIncluded.YES
            #     and MobileCase.android_app_url == ""
            # )

            column.formatted_data = getattr(mobile_case, column.source_attr)
            if isinstance(column.formatted_data, str):
                column.formatted_ui_data = column.formatted_data.replace(
                    IOS_ANDROID_SEPARATOR, "<br>"
                )
            else:
                column.formatted_ui_data = column.formatted_data
        else:
            column.formatted_data = format_model_field(
                source_instance=mobile_case, column=column
            )
            if column.edit_url_name is not None:
                column.edit_url = reverse(
                    column.edit_url_name, kwargs={"pk": mobile_case.id}
                )
                if column.edit_url_anchor:
                    column.edit_url += f"#{column.edit_url_anchor}"

    return columns


def csv_mobile_equality_body_output_generator(
    mobile_cases: QuerySet[MobileCase],
) -> Generator[str, None, None]:
    """
    Generate a series of strings containing the mobile equality body export data for
    a CSV streaming response
    """

    class DummyFile:
        def write(self, value_to_write):
            return value_to_write

    writer: Any = csv.writer(DummyFile())
    column_row: list[str] = [
        column.column_header for column in MOBILE_EQUALITY_BODY_COLUMNS_FOR_EXPORT
    ]

    output: str = writer.writerow(column_row)

    for counter, mobile_case in enumerate(mobile_cases):
        case_columns: list[EqualityBodyCSVColumn | MobileEqualityBodyCSVColumn] = (
            populate_mobile_equality_body_columns(mobile_case=mobile_case.get_case())
        )
        row = [column.formatted_data for column in case_columns]
        output += writer.writerow(row)
        if counter % DOWNLOAD_CASES_CHUNK_SIZE == 0:
            yield output
            output = ""
    if output:
        yield output
