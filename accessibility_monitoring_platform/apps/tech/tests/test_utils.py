"""Tests for tech team app utils"""

from dataclasses import dataclass
from datetime import date

import pytest
from django.contrib.auth.models import User

from ...cases.models import Sector
from ...mobile.models import MobileCase, MobileContact
from ..utils import create_mobile_case_from_dict


@dataclass
class KeyValueMapping:
    key: str
    value: str


ORGANISTION_NAME: str = "Organisation name"
ORGANISTION_URL: str = "https://orgisation.com"
APP_NAME: str = "App name"
APP_STORE_URL_IOS: str = "https://appstore.com/ios"
APP_STORE_URL_ANDROID: str = "https://appstore.com/android"
SECTOR_NAME: str = "Sector name"
ENFORCEMENT_BODY: str = "EHRC"
PUBLIC_SECTOR_BODY_LOCATION: str = "England"
PREVIOUS_CASE_URL: str = "https://domain.com/previous_case"
IS_COMPLAINT: str = "Yes"
CASE_FOLDER_URL: str = "https:/drive.com/case_folder"
IS_FEEDBACK_SURVEY_SENT: str = "Yes"
CONTACT_NAME: str = "Contact name"
CONTACT_TITLE: str = "Contact title"
CONTACT_DETAIL: str = "contact@domain.com"
FIRST_CONTACT_DATE: str = "1/01/1990"
INFORMATION_RECEIVED_DATE: str = "13/01/1992"
AUDITOR_NAME: str = "Auditor name"
TEST_START_DATE_IOS: str = "14/01/1992"
TEST_START_DATE_ANDROID: str = "15/01/1992"
TEST_END_DATE_IOS: str = "14/02/1992"
TEST_END_DATE_ANDROID: str = "15/02/1992"
NUMBER_OF_PAGES_TESTED_IOS: str = "17"
NUMBER_OF_PAGES_TESTED_ANDROID: str = "19"
NUMBER_OF_ISSUES_FOUND_IOS: str = "23"
NUMBER_OF_ISSUES_FOUND_ANDROID: str = "29"
INITIAL_APP_COMPLIANCE_IOS: KeyValueMapping = KeyValueMapping(
    key="not compliant", value=MobileCase.AppCompliance.NOT
)
INITIAL_APP_COMPLIANCE_ANDROID: KeyValueMapping = KeyValueMapping(
    key="", value=MobileCase.AppCompliance.UNKNOWN
)
INITIAL_STATEMENT_COMPLIANCE_IOS: KeyValueMapping = KeyValueMapping(
    key="not compliant", value=MobileCase.StatementCompliance.NOT_COMPLIANT
)
INITIAL_STATEMENT_COMPLIANCE_ANDROID: KeyValueMapping = KeyValueMapping(
    key="compliant", value=MobileCase.StatementCompliance.COMPLIANT
)
INITIAL_DISPROPORTIONATE_BURDEN_IOS: KeyValueMapping = KeyValueMapping(
    key="Claim with no assessment",
    value=MobileCase.DisproportionateBurden.NO_ASSESSMENT,
)
INITIAL_DISPROPORTIONATE_BURDEN_ANDROID: KeyValueMapping = KeyValueMapping(
    key="Claim with assessment", value=MobileCase.DisproportionateBurden.ASSESSMENT
)
REPORT_PDF_URL_IOS: str = "https:/drive.com/report_pdf_ios"
REPORT_PDF_URL_ANDROID: str = "https:/drive.com/report_pdf_android"
REPORT_SENT_ON: str = "16/02/1992"
ZENDESK_TICKET_URL: str = "https:/drive.com/zendesk_5"
FOLLOWUP_DATE_12_WEEK_DEADLINE: str = "17/02/1992"
REPORT_ACKNOWLEDGED_DATE: str = "18/02/1992"
TWELVE_WEEK_UPDATE_REQUESTED_DATE: str = "19/02/1992"
TWELVE_WEEK_UPDATE_RECEIVED_DATE: str = "20/02/1992"
RETEST_DATE_IOS: str = "21/02/1992"
RETEST_DATE_ANDROID: str = "22/02/1992"
NUMBER_OF_REMAINING_ISSUES_IOS: str = "1"
NUMBER_OF_REMAINING_ISSUES_ANDROID: str = "2"
RETEST_APP_COMPLIANCE_IOS: KeyValueMapping = KeyValueMapping(
    key="other", value=MobileCase.AppCompliance.UNKNOWN
)
RETEST_APP_COMPLIANCE_ANDROID: KeyValueMapping = KeyValueMapping(
    key="partially compliant", value=MobileCase.AppCompliance.PARTIALLY
)
RETEST_STATEMENT_COMPLIANCE_IOS: KeyValueMapping = KeyValueMapping(
    key="other", value=MobileCase.StatementCompliance.UNKNOWN
)
RETEST_STATEMENT_COMPLIANCE_ANDROID: KeyValueMapping = KeyValueMapping(
    key="no statement", value=MobileCase.StatementCompliance.NO_STATEMENT
)
RETEST_STATEMENT_COMPLIANCE_NOTES_IOS: str = "Notes on accessibility statement (iOS)"
RETEST_STATEMENT_COMPLIANCE_NOTES_ANDROID: str = (
    "Notes on accessibility statement (Android)"
)
RETEST_DISPROPORTIONATE_BURDEN_IOS: KeyValueMapping = KeyValueMapping(
    key="No claim", value=MobileCase.DisproportionateBurden.NO_CLAIM
)
RETEST_DISPROPORTIONATE_BURDEN_ANDROID: KeyValueMapping = KeyValueMapping(
    key="No statement", value=MobileCase.DisproportionateBurden.NO_STATEMENT
)
DISPROPORTIONATE_BURDEN_NOTES_IOS: str = "Notes on Disproportionate Burden (iOS)"
DISPROPORTIONATE_BURDEN_NOTES_ANDROID: str = (
    "Notes on Disproportionate Burden (Android)"
)
SUMMARY_OF_PROGRESS: str = "Summary of progress made by PSB"
ENFORCEMENT_RECOMMENDATION_IOS: KeyValueMapping = KeyValueMapping(
    key="No further action",
    value=MobileCase.RecommendationForEnforcement.NO_FURTHER_ACTION,
)
ENFORCEMENT_RECOMMENDATION_ANDROID: str = MobileCase.RecommendationForEnforcement.OTHER
ENFORCEMENT_RECOMMENDATION_NOTES: str = "Enforcement Recommendation notes"
DATE_DECISION_EMAIL_SENT: str = "23/02/1992"
DECISION_SENT_TO: str = "Decision sent to name"
ADDED_TO_STATS_TAB: str = "Yes"
COPY_OF_STATEMENT_URL: str = "https:/drive.com/new_statement"
DATE_SENT_TO_ENFORCEMENT_BODY: str = "24/02/1992"
ENFORCEMENT_BODY_STATE: KeyValueMapping = KeyValueMapping(
    key="Yes", value=MobileCase.EnforcementBodyClosedCase.IN_PROGRESS
)
ROW: dict[str, str] = {
    "Record ": "M1",
    "Status": "Case closed and sent to equality body",
    "Organisation URL": ORGANISTION_URL,
    "Organisation name": ORGANISTION_NAME,
    "Parent org (if relevant)": "",
    "App name ": APP_NAME,
    "URL (iOS)": APP_STORE_URL_IOS,
    "URL (Android)": APP_STORE_URL_ANDROID,
    "Type": "Combined",
    "Sector": SECTOR_NAME,
    "Sub-category": "",
    "Enforcement body": ENFORCEMENT_BODY,
    "Public sector body location": PUBLIC_SECTOR_BODY_LOCATION,
    "URL to previous case ": PREVIOUS_CASE_URL,
    "Is it a complaint?": IS_COMPLAINT,
    "Link to case folder": CASE_FOLDER_URL,
    "Feedback survey sent ": IS_FEEDBACK_SURVEY_SENT,
    "Contact name": CONTACT_NAME,
    "Job title": CONTACT_TITLE,
    "Contact detail": CONTACT_DETAIL,
    "First contact date": FIRST_CONTACT_DATE,
    "Information received": INFORMATION_RECEIVED_DATE,
    "Auditor": AUDITOR_NAME,
    "Test start date (iOS)": TEST_START_DATE_IOS,
    "Test start date (Android)": TEST_START_DATE_ANDROID,
    "Link to monitor doc": "https:/drive.com/monitor_doc_folder",
    "Test end date (iOS)": TEST_END_DATE_IOS,
    "Test end date (Android)": TEST_END_DATE_ANDROID,
    "Number of pages tested (iOS)": NUMBER_OF_PAGES_TESTED_IOS,
    "Number of pages tested (Android)": NUMBER_OF_PAGES_TESTED_ANDROID,
    "Number of issues found (iOS)": NUMBER_OF_ISSUES_FOUND_IOS,
    "Number of issues found (Android)": NUMBER_OF_ISSUES_FOUND_ANDROID,
    "Initial app compliance decision (iOS)": INITIAL_APP_COMPLIANCE_IOS.key,
    "Initial app compliance decision (Android)": INITIAL_APP_COMPLIANCE_ANDROID.key,
    "Initial statement compliance decision (iOS)": INITIAL_STATEMENT_COMPLIANCE_IOS.key,
    "Initial statement compliance decision (Android)": INITIAL_STATEMENT_COMPLIANCE_ANDROID.key,
    "Initial disproportionate burden claim (iOS)": INITIAL_DISPROPORTIONATE_BURDEN_IOS.key,
    "Initial disproportionate burden claim (Android)": INITIAL_DISPROPORTIONATE_BURDEN_ANDROID.key,
    "Report checked by": AUDITOR_NAME,
    "Public link to report PDF (iOS)": REPORT_PDF_URL_IOS,
    "Public link to report PDF (Android)": REPORT_PDF_URL_ANDROID,
    "Days taken to test": "2",
    "Report sent on": REPORT_SENT_ON,
    "Zendesk ticket": ZENDESK_TICKET_URL,
    "Followup date - 12 week deadline": FOLLOWUP_DATE_12_WEEK_DEADLINE,
    "Report acknowledged": REPORT_ACKNOWLEDGED_DATE,
    "12-week update requested": TWELVE_WEEK_UPDATE_REQUESTED_DATE,
    "12-week update received": TWELVE_WEEK_UPDATE_RECEIVED_DATE,
    "Retest date (iOS)": RETEST_DATE_IOS,
    "Retest date (Android)": RETEST_DATE_ANDROID,
    "Total number of remaining issues (iOS)": NUMBER_OF_REMAINING_ISSUES_IOS,
    "Total number of remaining issues (Android)": NUMBER_OF_REMAINING_ISSUES_ANDROID,
    "Retest app compliance decision (iOS)": RETEST_APP_COMPLIANCE_IOS.key,
    "Retest app compliance decision (Android)": RETEST_APP_COMPLIANCE_ANDROID.key,
    "(remove)": "",
    "Accessibility Statement Decision (iOS)": RETEST_STATEMENT_COMPLIANCE_IOS.key,
    "Accessibility Statement Decision (Android)": RETEST_STATEMENT_COMPLIANCE_ANDROID.key,
    "Notes on accessibility statement (iOS)": RETEST_STATEMENT_COMPLIANCE_NOTES_IOS,
    "Notes on accessibility statement (Android)": RETEST_STATEMENT_COMPLIANCE_NOTES_ANDROID,
    "Disproportionate Burden Claimed? (iOS)": RETEST_DISPROPORTIONATE_BURDEN_IOS.key,
    "Disproportionate Burden Claimed? (Android)": RETEST_DISPROPORTIONATE_BURDEN_ANDROID.key,
    "Disproportionate Burden Notes (iOS)": DISPROPORTIONATE_BURDEN_NOTES_IOS,
    "Disproportionate Burden Notes (Android)": DISPROPORTIONATE_BURDEN_NOTES_ANDROID,
    "Summary of progress made / response from PSB": SUMMARY_OF_PROGRESS,
    "Enforcement Recommendation (iOS)": ENFORCEMENT_RECOMMENDATION_IOS.key,
    "Enforcement Recommendation (Android)": ENFORCEMENT_RECOMMENDATION_ANDROID,
    "Enforcement Recommendation Notes (iOS)": ENFORCEMENT_RECOMMENDATION_NOTES,
    "Enforcement Recommendation Notes (Android)": "",
    "Date decision email sent": DATE_DECISION_EMAIL_SENT,
    "Decision sent to": DECISION_SENT_TO,
    "Added to stats tab (formula)": ADDED_TO_STATS_TAB,
    "Link to new copy of accessibility statement if not compliant": COPY_OF_STATEMENT_URL,
    "Percentage of issues resolved (iOS)": "43%",
    "Percentage of issues resolved (Android)": "47%",
    "Date sent to enforcement body": DATE_SENT_TO_ENFORCEMENT_BODY,
    "Active case with enforcement body?": ENFORCEMENT_BODY_STATE.key,
    "Reporting year": "2022",
}


def get_date_from_string(date_string: str) -> date:
    day, month, year = date_string.split("/")
    return date(int(year), int(month), int(day))


@pytest.mark.django_db
def test_create_mobile_case_from_dict():
    """Test creation of mobile case from dictionary of imported data"""
    user: User = User.objects.create()
    sector: Sector = Sector.objects.create(name=SECTOR_NAME)

    create_mobile_case_from_dict(
        row=ROW,
        default_user=user,
        auditors={AUDITOR_NAME: user},
        sectors={SECTOR_NAME: sector},
    )

    mobile_case: MobileCase = MobileCase.objects.all().first()

    assert mobile_case.organisation_name == ORGANISTION_NAME
    assert mobile_case.app_name == APP_NAME
    assert mobile_case.ios_app_store_url == APP_STORE_URL_IOS
    assert mobile_case.android_app_store_url == APP_STORE_URL_ANDROID
    assert mobile_case.sector == sector
    assert mobile_case.enforcement_body == ENFORCEMENT_BODY.lower()
    assert mobile_case.psb_location == PUBLIC_SECTOR_BODY_LOCATION.lower()
    assert mobile_case.previous_case_url == PREVIOUS_CASE_URL
    assert mobile_case.is_complaint == IS_COMPLAINT.lower()
    assert mobile_case.case_folder_url == CASE_FOLDER_URL
    assert mobile_case.is_feedback_requested == IS_FEEDBACK_SURVEY_SENT.lower()

    mobile_contact: MobileContact = mobile_case.contacts.first()

    assert mobile_contact.name == CONTACT_NAME
    assert mobile_contact.job_title == CONTACT_TITLE
    assert mobile_contact.contact_details == CONTACT_DETAIL

    assert mobile_case.contact_information_request_start_date == get_date_from_string(
        FIRST_CONTACT_DATE
    )
    assert mobile_case.contact_information_request_end_date == get_date_from_string(
        INFORMATION_RECEIVED_DATE
    )
    assert mobile_case.auditor == user
    assert mobile_case.initial_ios_test_start_date == get_date_from_string(
        TEST_START_DATE_IOS
    )
    assert mobile_case.initial_android_test_start_date == get_date_from_string(
        TEST_START_DATE_ANDROID
    )
    # assert mobile_case. == MONITOR_DOC_FOLDER_URL
    assert mobile_case.initial_ios_test_end_date == get_date_from_string(
        TEST_END_DATE_IOS
    )
    assert mobile_case.initial_android_test_end_date == get_date_from_string(
        TEST_END_DATE_ANDROID
    )
    assert mobile_case.initial_ios_total_number_of_pages == int(
        NUMBER_OF_PAGES_TESTED_IOS
    )
    assert mobile_case.initial_android_total_number_of_pages == int(
        NUMBER_OF_PAGES_TESTED_ANDROID
    )
    assert mobile_case.initial_ios_total_number_of_issues == int(
        NUMBER_OF_ISSUES_FOUND_IOS
    )
    assert mobile_case.initial_android_total_number_of_issues == int(
        NUMBER_OF_ISSUES_FOUND_ANDROID
    )
    assert (
        mobile_case.initial_ios_app_compliance_state == INITIAL_APP_COMPLIANCE_IOS.value
    )
    assert (
        mobile_case.initial_android_app_compliance_state
        == INITIAL_APP_COMPLIANCE_ANDROID.value
    )
    assert (
        mobile_case.initial_ios_statement_compliance_state
        == INITIAL_STATEMENT_COMPLIANCE_IOS.value
    )
    assert (
        mobile_case.initial_android_statement_compliance_state
        == INITIAL_STATEMENT_COMPLIANCE_ANDROID.value
    )
    assert (
        mobile_case.initial_ios_disproportionate_burden_claim
        == INITIAL_DISPROPORTIONATE_BURDEN_IOS.value
    )
    assert (
        mobile_case.initial_android_disproportionate_burden_claim
        == INITIAL_DISPROPORTIONATE_BURDEN_ANDROID.value
    )
    assert mobile_case.equality_body_report_url_ios == REPORT_PDF_URL_IOS
    assert mobile_case.equality_body_report_url_android == REPORT_PDF_URL_ANDROID
    assert mobile_case.report_sent_date == get_date_from_string(REPORT_SENT_ON)
    # assert mobile_case. == ZENDESK_TICKET_URL
    assert mobile_case.twelve_week_deadline_date == get_date_from_string(
        FOLLOWUP_DATE_12_WEEK_DEADLINE
    )
    assert mobile_case.report_acknowledged_date == get_date_from_string(
        REPORT_ACKNOWLEDGED_DATE
    )
    assert mobile_case.twelve_week_update_date == get_date_from_string(
        TWELVE_WEEK_UPDATE_REQUESTED_DATE
    )
    assert mobile_case.twelve_week_received_date == get_date_from_string(
        TWELVE_WEEK_UPDATE_RECEIVED_DATE
    )
    assert mobile_case.retest_ios_start_date == get_date_from_string(RETEST_DATE_IOS)
    assert mobile_case.retest_android_start_date == get_date_from_string(
        RETEST_DATE_ANDROID
    )
    assert mobile_case.retest_ios_total_number_of_issues == int(
        NUMBER_OF_REMAINING_ISSUES_IOS
    )
    assert mobile_case.retest_android_total_number_of_issues == int(
        NUMBER_OF_REMAINING_ISSUES_ANDROID
    )
    assert (
        mobile_case.retest_ios_app_compliance_state == RETEST_APP_COMPLIANCE_IOS.value
    )
    assert (
        mobile_case.retest_android_app_compliance_state
        == RETEST_APP_COMPLIANCE_ANDROID.value
    )
    assert (
        mobile_case.retest_ios_statement_compliance_state
        == RETEST_STATEMENT_COMPLIANCE_IOS.value
    )
    assert (
        mobile_case.retest_android_statement_compliance_state
        == RETEST_STATEMENT_COMPLIANCE_ANDROID.value
    )
    assert (
        mobile_case.retest_ios_statement_compliance_information
        == RETEST_STATEMENT_COMPLIANCE_NOTES_IOS
    )
    assert (
        mobile_case.retest_android_statement_compliance_information
        == RETEST_STATEMENT_COMPLIANCE_NOTES_ANDROID
    )
    assert (
        mobile_case.retest_ios_disproportionate_burden_claim
        == RETEST_DISPROPORTIONATE_BURDEN_IOS.value
    )
    assert (
        mobile_case.retest_android_disproportionate_burden_claim
        == RETEST_DISPROPORTIONATE_BURDEN_ANDROID.value
    )
    assert (
        mobile_case.retest_ios_disproportionate_burden_information
        == DISPROPORTIONATE_BURDEN_NOTES_IOS
    )
    assert (
        mobile_case.retest_android_disproportionate_burden_information
        == DISPROPORTIONATE_BURDEN_NOTES_ANDROID
    )
    assert mobile_case.psb_progress_info == SUMMARY_OF_PROGRESS
    assert (
        mobile_case.recommendation_for_enforcement
        == ENFORCEMENT_RECOMMENDATION_IOS.value
    )
    # assert mobile_case. == ENFORCEMENT_RECOMMENDATION_ANDROID
    assert mobile_case.recommendation_info == ENFORCEMENT_RECOMMENDATION_NOTES
    assert mobile_case.recommendation_decision_sent_date == get_date_from_string(
        DATE_DECISION_EMAIL_SENT
    )
    assert mobile_case.recommendation_decision_sent_to == DECISION_SENT_TO
    assert mobile_case.is_case_added_to_stats == ADDED_TO_STATS_TAB.lower()
    # assert mobile_case. == COPY_OF_STATEMENT_URL
    assert mobile_case.enforcement_body_sent_date == get_date_from_string(
        DATE_SENT_TO_ENFORCEMENT_BODY
    )
    assert (
        mobile_case.enforcement_body_closed_case_state == ENFORCEMENT_BODY_STATE.value
    )
