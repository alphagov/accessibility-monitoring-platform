"""
Test template for integration tests
"""

import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import Select
from app.parse_json import parse_integration_tests_json
import argparse

parser = argparse.ArgumentParser(description="Settings for integration tests")

parser.add_argument(
    "-s"
    "--settings-json",
    dest="settings_json",
    help="Path for json settings"
)

args = parser.parse_args()

settings = parse_integration_tests_json(settings_path=args.settings_json)

ORGANISATION_NAME = "Example Organisation"
HOME_PAGE_URL = "https://example.com"
ENFORCEMENT_BODY_VALUE = "ehrc"
ENFORCEMENT_BODY_LABEL = "Equality and Human Rights Commission"
ZENDESK_URL = "https://zendesk.com"
TRELLO_URL = "https://trello.com"
CASE_DETAILS_NOTES = """I am
a multiline
case details note, I am"""

CONTACT_FIRST_NAME = "Contact first name"
CONTACT_LAST_NAME = "Contact last name"
CONTACT_JOB_TITLE = "Contact title"
EMAIL = "contact_email@example.com"
CONTACT_NOTES = """I am
a multiline
contact note, I am"""

TEST_RESULTS_URL = "https://test-results.com"
ACCESSIBILITY_STATEMENT_STATUS = "missing"
ACCESSIBILITY_STATEMENT_NOTES = """I am
a multiline
accessibility statement note, I am"""
WEBSITE_COMPLIANCE_NOTES = """I am
a multiline
accessibility statement note, I am"""


REPORT_DRAFT_URL = "https://report-draft.com"
REPORT_NOTES = """I am
a multiline
report note, I am"""

REPORT_REVIEWER_NOTES = """I am
a multiline
report reviewer note, I am"""
REPORT_FINAL_PDF_URL = "https://report-final-pdf.com"
REPORT_FINAL_ODT_URL = "https://report-final-odt.com"

REPORT_SENT_DATE_DD = "31"
REPORT_SENT_DATE_MM = "12"
REPORT_SENT_DATE_YYYY = "2020"
REPORT_ACKNOWLEGED_DATE_DD = "1"
REPORT_ACKNOWLEGED_DATE_MM = "4"
REPORT_ACKNOWLEGED_DATE_YYYY = "2021"
REPORT_CORRESPONDENCE_NOTES = """I am
a multiline
report correspondence note, I am"""

TWELVE_WEEK_UPDATE_REQUESTED_DD = "1"
TWELVE_WEEK_UPDATE_REQUESTED_MM = "3"
TWELVE_WEEK_UPDATE_REQUESTED_YYYY = "2021"
TWELVE_WEEK_ACKNOWLEGED_DATE_DD = "1"
TWELVE_WEEK_ACKNOWLEGED_DATE_MM = "7"
TWELVE_WEEK_ACKNOWLEGED_DATE_YYYY = "2021"
TWELVE_WEEK_CORRESPONDENCE_NOTES = """I am
a multiline
12 week correspondence note, I am"""

PSB_PROGRESS_NOTES = """I am
a multiline
public sector body progress note, I am"""
RETESTED_WEBSITE_DD = "1"
RETESTED_WEBSITE_MM = "8"
RETESTED_WEBSITE_YYYY = "2021"
DISPROPORTIONATE_NOTES = """I am
a multiline
disproportionate burden note, I am"""
ACCESSIBILITY_STATEMENT_NOTES_FINAL = """I am
a multiline
accessibility statement final note, I am"""
RECOMMENDATION_NOTES = """I am
a multiline
recommendation note, I am"""
COMPLIANCE_EMAIL_SENT_DATE_DD = "13"
COMPLIANCE_EMAIL_SENT_DATE_MM = "8"
COMPLIANCE_EMAIL_SENT_DATE_YYYY = "2021"

PSB_APPEAL_NOTES = """I am
a multiline
public sector body appeal note, I am"""
SENT_TO_ENFORCEMENT_BODY_SENT_DATE_DD = "15"
SENT_TO_ENFORCEMENT_BODY_SENT_DATE_MM = "8"
SENT_TO_ENFORCEMENT_BODY_SENT_DATE_YYYY = "2021"
ENFORCEMENT_BODY_CORRESPONDENCE_NOTES = """I am
a multiline
enforcement body correspondence note, I am"""

REPORT_FOLLOWUP_WEEK_1_DUE_DATE_DD = "16"
REPORT_FOLLOWUP_WEEK_1_DUE_DATE_MM = "8"
REPORT_FOLLOWUP_WEEK_1_DUE_DATE_YYYY = "2021"
REPORT_FOLLOWUP_WEEK_4_DUE_DATE_DD = "20"
REPORT_FOLLOWUP_WEEK_4_DUE_DATE_MM = "8"
REPORT_FOLLOWUP_WEEK_4_DUE_DATE_YYYY = "2021"
REPORT_FOLLOWUP_WEEK_12_DUE_DATE_DD = "31"
REPORT_FOLLOWUP_WEEK_12_DUE_DATE_MM = "8"
REPORT_FOLLOWUP_WEEK_12_DUE_DATE_YYYY = "2021"

REPORT_FOLLOWUP_WEEK_12_DUE_DATE2_DD = "13"
REPORT_FOLLOWUP_WEEK_12_DUE_DATE2_MM = "7"
REPORT_FOLLOWUP_WEEK_12_DUE_DATE2_YYYY = "2021"
TWELVE_WEEK_1_WEEK_CHASER_DUE_DATE_DD = "20"
TWELVE_WEEK_1_WEEK_CHASER_DUE_DATE_MM = "7"
TWELVE_WEEK_1_WEEK_CHASER_DUE_DATE_YYYY = "2021"
TWELVE_WEEK_4_WEEK_CHASER_DUE_DATE_DD = "24"
TWELVE_WEEK_4_WEEK_CHASER_DUE_DATE_MM = "7"
TWELVE_WEEK_4_WEEK_CHASER_DUE_DATE_YYYY = "2021"

DELETE_NOTES = """I am
a multiline
deletion note, I am"""

ORGANISATION_NAME_TO_DELETE = "Example Organisation to Delete"
HOME_PAGE_URL_TO_DELETE = "https://example-to-delete.com"


class SeleniumTest(unittest.TestCase):
    """
    Test case for integration tests

    Methods
    -------
    setUp()
        Setup selenium webdriver
    login()
        Login to platform
    """

    def setUp(self):
        """Setup selenium test environment"""
        options: Options = Options()
        if settings["headless"]:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        self.driver: WebDriver = webdriver.Chrome(
            executable_path=f"""./stack_tests/chromedriver_{settings["chrome_version"]}""",
            options=options
        )

    def login(self):
        """Login in to platform"""
        self.driver.get("http://localhost:8001/accounts/login/?next=/")
        self.driver.find_element_by_name("username").send_keys("admin@email.com")
        self.driver.find_element_by_name("password").send_keys("secret")
        self.driver.find_element_by_xpath('//input[@value="Submit"]').click()


class TestLogin(SeleniumTest):
    """
    Test case for integration tests of login

    Methods
    -------
    test_login()
        Tests whether user can login
    """

    def test_login(self):
        """Tests whether user can login"""
        self.login()
        self.assertEqual(
            '<h1 class="govuk-heading-xl">Your cases</h1>' in self.driver.page_source,
            True,
        )


class TestCases(SeleniumTest):
    """
    Test case for integration tests of case creation

    Methods
    -------
    setUp()
        Login and navigate to Cases list
    """

    def setUp(self):
        """Setup selenium test environment; Login and navigate to Cases list"""
        super().setUp()
        self.login()
        self.driver.find_element_by_link_text("Search").click()


class TestCaseCreation(TestCases):
    """
    Test case for integration tests of case creation

    Methods
    -------
    test_create_case()
        Tests whether case can be created
    test_duplicate_case_found()
        Tests whether duplicate case is found
    """

    def test_create_case(self):
        """Tests whether case can be created"""
        self.driver.find_element_by_link_text("Create case").click()
        self.driver.find_element_by_name("organisation_name").send_keys(
            ORGANISATION_NAME
        )
        self.driver.find_element_by_name("home_page_url").send_keys(HOME_PAGE_URL)
        self.driver.find_element_by_css_selector(
            f"input[type='radio'][value='{ENFORCEMENT_BODY_VALUE}']"
        ).click()
        self.driver.find_element_by_css_selector("#id_is_complaint").click()
        self.driver.find_element_by_name("save_exit").click()
        self.assertTrue(
            '<h1 class="govuk-heading-xl">Search</h1>' in self.driver.page_source
        )
        self.assertTrue(ORGANISATION_NAME in self.driver.page_source)

    def test_duplicate_case_found(self):
        """Tests whether duplicate case is found"""
        self.driver.find_element_by_link_text("Create case").click()
        self.driver.find_element_by_name("organisation_name").send_keys(
            ORGANISATION_NAME
        )
        self.driver.find_element_by_name("home_page_url").send_keys(HOME_PAGE_URL)
        self.driver.find_element_by_css_selector(
            f"input[type='radio'][value='{ENFORCEMENT_BODY_VALUE}']"
        ).click()
        self.driver.find_element_by_name("save_exit").click()
        self.assertTrue(
            '<h1 class="govuk-heading-xl">Create case</h1>' in self.driver.page_source
        )
        self.assertTrue(
            "We have found 1 cases matching the details you have given"
            in self.driver.page_source
        )


class TestCaseUpdates(TestCases):
    """
    Test case for integration tests of case updates

    Methods
    -------
    setUp()
        Create case to update
    test_update_case_sections()
        Tests whether all case sections can be updated
    test_update_case_edit_case_details()
        Tests whether case details can be updated
    test_update_case_edit_contact_details()
        Tests whether contact details can be updated
    test_update_case_edit_testing_details()
        Tests whether testing details can be updated
    test_update_case_edit_report_details()
        Tests whether report details can be updated
    test_update_case_edit_qa_process()
        Tests whether QA process can be updated
    test_update_case_edit_report_correspondence()
        Tests whether report correspondence can be updated
    test_update_case_edit_12_week_correspondence()
        Tests whether 12 week correspondence can be updated
    test_update_case_edit_final_decision()
        Tests whether final decision can be updated
    test_update_case_edit_enforcement_body_correspondence()
        Tests whether enforcement body correspondence can be updated
    test_update_case_edit_psb_is_unresponsive()
        Tests whether unresponsive public sector bodies can be moved directly to enforcement body
    """

    def setUp(self):
        """Create case to update"""
        super().setUp()
        self.driver.find_element_by_link_text("Create case").click()
        self.driver.find_element_by_name("organisation_name").send_keys(
            ORGANISATION_NAME
        )
        self.driver.find_element_by_name("home_page_url").send_keys(HOME_PAGE_URL)
        self.driver.find_element_by_css_selector(
            f"input[type='radio'][value='{ENFORCEMENT_BODY_VALUE}']"
        ).click()
        self.driver.find_element_by_name("save_exit").click()
        self.driver.find_element_by_link_text(ORGANISATION_NAME).click()

    def test_update_case_edit_case_details(self):
        """Tests whether case details can be updated"""
        self.driver.find_element_by_link_text("Edit case details").click()

        self.assertTrue(">Case details</h1>" in self.driver.page_source)
        self.driver.find_element_by_css_selector(
            f"input[type='radio'][value='{ENFORCEMENT_BODY_VALUE}']"
        ).click()
        self.driver.find_element_by_css_selector(
            "input[type='radio'][value='england']"
        ).click()
        self.driver.find_element_by_css_selector("#id_is_complaint").click()
        self.driver.find_element_by_name("trello_url").send_keys(TRELLO_URL)
        self.driver.find_element_by_name("notes").send_keys(CASE_DETAILS_NOTES)
        self.driver.find_element_by_css_selector(
            "#id_case_details_complete_date"
        ).click()
        self.driver.find_element_by_name("save").click()
        self.driver.find_element_by_link_text("Case").click()

        self.assertTrue(">View case</h1>" in self.driver.page_source)
        self.assertTrue(ENFORCEMENT_BODY_LABEL in self.driver.page_source)
        self.assertTrue(TRELLO_URL in self.driver.page_source)
        self.assertTrue(CASE_DETAILS_NOTES in self.driver.page_source)

    def test_update_case_edit_contact_details(self):
        """Tests whether contact details can be updated"""
        self.driver.find_element_by_link_text("Edit contact details").click()

        self.assertTrue(">Contact details</h1>" in self.driver.page_source)
        self.driver.find_element_by_xpath('//input[@value="Create contact"]').click()

        self.driver.find_element_by_name("form-0-first_name").send_keys(
            CONTACT_FIRST_NAME
        )
        self.driver.find_element_by_name("form-0-last_name").send_keys(
            CONTACT_LAST_NAME
        )
        self.driver.find_element_by_name("form-0-job_title").send_keys(
            CONTACT_JOB_TITLE
        )
        self.driver.find_element_by_name("form-0-email").send_keys(EMAIL)
        self.driver.find_element_by_name("form-0-notes").send_keys(CONTACT_NOTES)
        self.driver.find_element_by_css_selector(
            "#id_contact_details_complete_date"
        ).click()
        self.driver.find_element_by_name("save").click()
        self.driver.find_element_by_link_text("Case").click()

        self.assertTrue(">View case</h1>" in self.driver.page_source)
        self.assertTrue(CONTACT_FIRST_NAME in self.driver.page_source)
        self.assertTrue(CONTACT_LAST_NAME in self.driver.page_source)
        self.assertTrue(CONTACT_JOB_TITLE in self.driver.page_source)
        self.assertTrue(EMAIL in self.driver.page_source)
        self.assertTrue(CONTACT_NOTES in self.driver.page_source)

    def test_update_case_edit_testing_details(self):
        """Tests whether testing details can be updated"""
        self.driver.find_element_by_link_text("Edit testing details").click()

        self.assertTrue(">Testing details</h1>" in self.driver.page_source)
        self.driver.find_element_by_name("accessibility_statement_notes").send_keys(
            TEST_RESULTS_URL
        )
        self.driver.find_element_by_css_selector("#id_test_status_0").click()
        self.driver.find_element_by_css_selector(
            "#id_accessibility_statement_state_3"
        ).click()
        self.driver.find_element_by_name("accessibility_statement_notes").send_keys(
            ACCESSIBILITY_STATEMENT_NOTES
        )
        self.driver.find_element_by_css_selector("#id_is_website_compliant_1").click()
        self.driver.find_element_by_name("accessibility_statement_notes").send_keys(
            WEBSITE_COMPLIANCE_NOTES
        )
        self.driver.find_element_by_css_selector(
            "#id_testing_details_complete_date"
        ).click()
        self.driver.find_element_by_name("save").click()
        self.driver.find_element_by_link_text("Case").click()

        self.assertTrue(">View case</h1>" in self.driver.page_source)
        self.assertTrue(TEST_RESULTS_URL in self.driver.page_source)
        self.assertTrue(ACCESSIBILITY_STATEMENT_NOTES in self.driver.page_source)
        self.assertTrue(WEBSITE_COMPLIANCE_NOTES in self.driver.page_source)

    def test_update_case_edit_report_details(self):
        """Tests whether report details can be updated"""
        self.driver.find_element_by_link_text("Edit report details").click()

        self.assertTrue(">Report details</h1>" in self.driver.page_source)
        self.driver.find_element_by_name("report_draft_url").send_keys(REPORT_DRAFT_URL)
        self.driver.find_element_by_css_selector("#id_report_review_status_1").click()
        self.driver.find_element_by_name("report_notes").send_keys(
            REPORT_NOTES
        )

        self.driver.find_element_by_css_selector(
            "#id_reporting_details_complete_date"
        ).click()
        self.driver.find_element_by_name("save").click()
        self.driver.find_element_by_link_text("Case").click()

        self.assertTrue(">View case</h1>" in self.driver.page_source)
        self.assertTrue(REPORT_DRAFT_URL in self.driver.page_source)
        self.assertTrue(REPORT_NOTES in self.driver.page_source)

    def test_update_case_edit_qa_process(self):
        """Tests whether QA process can be updated"""
        self.driver.find_element_by_link_text("Edit QA process").click()

        self.assertTrue(">QA process</h1>" in self.driver.page_source)
        self.driver.find_element_by_css_selector("#id_report_approved_status_1").click()
        self.driver.find_element_by_name("reviewer_notes").send_keys(
            REPORT_REVIEWER_NOTES
        )
        self.driver.find_element_by_name("report_final_pdf_url").send_keys(
            REPORT_FINAL_PDF_URL
        )
        self.driver.find_element_by_name("report_final_odt_url").send_keys(
            REPORT_FINAL_ODT_URL
        )
        self.driver.find_element_by_css_selector(
            "#id_qa_process_complete_date"
        ).click()
        self.driver.find_element_by_name("save").click()
        self.driver.find_element_by_link_text("Case").click()

        self.assertTrue(">View case</h1>" in self.driver.page_source)
        self.assertTrue(REPORT_REVIEWER_NOTES in self.driver.page_source)
        self.assertTrue(REPORT_FINAL_PDF_URL in self.driver.page_source)
        self.assertTrue(REPORT_FINAL_ODT_URL in self.driver.page_source)

    def test_update_case_edit_report_correspondence(self):
        """Tests whether report correspondence can be updated"""
        self.driver.find_element_by_link_text("Edit report correspondence").click()

        self.assertTrue(
            ">Report correspondence</h1>" in self.driver.page_source
        )

        self.driver.find_element_by_name("report_sent_date_0").clear()
        self.driver.find_element_by_name("report_sent_date_0").send_keys(
            REPORT_SENT_DATE_DD
        )
        self.driver.find_element_by_name("report_sent_date_1").clear()
        self.driver.find_element_by_name("report_sent_date_1").send_keys(
            REPORT_SENT_DATE_MM
        )
        self.driver.find_element_by_name("report_sent_date_2").clear()
        self.driver.find_element_by_name("report_sent_date_2").send_keys(
            REPORT_SENT_DATE_YYYY
        )

        self.driver.find_element_by_name("report_acknowledged_date_0").clear()
        self.driver.find_element_by_name("report_acknowledged_date_0").send_keys(
            REPORT_ACKNOWLEGED_DATE_DD
        )
        self.driver.find_element_by_name("report_acknowledged_date_1").clear()
        self.driver.find_element_by_name("report_acknowledged_date_1").send_keys(
            REPORT_ACKNOWLEGED_DATE_MM
        )
        self.driver.find_element_by_name("report_acknowledged_date_2").clear()
        self.driver.find_element_by_name("report_acknowledged_date_2").send_keys(
            REPORT_ACKNOWLEGED_DATE_YYYY
        )

        self.driver.find_element_by_name("zendesk_url").send_keys(ZENDESK_URL)
        self.driver.find_element_by_name("correspondence_notes").send_keys(
            REPORT_CORRESPONDENCE_NOTES
        )
        self.driver.find_element_by_css_selector(
            "#id_report_correspondence_complete_date"
        ).click()

        self.driver.find_element_by_name("save").click()
        self.driver.find_element_by_link_text("Case").click()

        self.assertTrue(">View case</h1>" in self.driver.page_source)
        self.assertTrue("31/12/2020" in self.driver.page_source)
        self.assertTrue("01/04/2021" in self.driver.page_source)
        self.assertTrue(ZENDESK_URL in self.driver.page_source)
        self.assertTrue(REPORT_CORRESPONDENCE_NOTES in self.driver.page_source)

        # Check due dates have been calculated
        self.driver.find_element_by_link_text("Edit report correspondence").click()
        self.assertTrue(
            "Due 07/01/2021" in self.driver.page_source
        )  # 1 week followup date
        self.assertTrue(
            "Due 28/01/2021" in self.driver.page_source
        )  # 4 week followup date
        self.assertTrue("Due 25/03/2021" in self.driver.page_source)  # 12 week deadline

    def test_update_case_edit_12_week_correspondence(self):
        """Tests whether 12 week correspondence can be updated"""
        self.driver.find_element_by_link_text("Edit report correspondence").click()
        self.driver.find_element_by_name("report_sent_date_0").clear()
        self.driver.find_element_by_name("report_sent_date_0").send_keys(
            REPORT_SENT_DATE_DD
        )
        self.driver.find_element_by_name("report_sent_date_1").clear()
        self.driver.find_element_by_name("report_sent_date_1").send_keys(
            REPORT_SENT_DATE_MM
        )
        self.driver.find_element_by_name("report_sent_date_2").clear()
        self.driver.find_element_by_name("report_sent_date_2").send_keys(
            REPORT_SENT_DATE_YYYY
        )
        self.driver.find_element_by_name("save").click()
        self.driver.find_element_by_link_text("Case").click()

        self.driver.find_element_by_link_text("Edit 12 week correspondence").click()

        self.assertTrue(
            ">12 week correspondence</h1>" in self.driver.page_source
        )

        self.driver.find_element_by_name("twelve_week_update_requested_date_0").clear()
        self.driver.find_element_by_name(
            "twelve_week_update_requested_date_0"
        ).send_keys(TWELVE_WEEK_UPDATE_REQUESTED_DD)
        self.driver.find_element_by_name("twelve_week_update_requested_date_1").clear()
        self.driver.find_element_by_name(
            "twelve_week_update_requested_date_1"
        ).send_keys(TWELVE_WEEK_UPDATE_REQUESTED_MM)
        self.driver.find_element_by_name("twelve_week_update_requested_date_2").clear()
        self.driver.find_element_by_name(
            "twelve_week_update_requested_date_2"
        ).send_keys(TWELVE_WEEK_UPDATE_REQUESTED_YYYY)

        self.driver.find_element_by_name(
            "twelve_week_correspondence_acknowledged_date_0"
        ).clear()
        self.driver.find_element_by_name(
            "twelve_week_correspondence_acknowledged_date_0"
        ).send_keys(TWELVE_WEEK_ACKNOWLEGED_DATE_DD)
        self.driver.find_element_by_name(
            "twelve_week_correspondence_acknowledged_date_1"
        ).clear()
        self.driver.find_element_by_name(
            "twelve_week_correspondence_acknowledged_date_1"
        ).send_keys(TWELVE_WEEK_ACKNOWLEGED_DATE_MM)
        self.driver.find_element_by_name(
            "twelve_week_correspondence_acknowledged_date_2"
        ).clear()
        self.driver.find_element_by_name(
            "twelve_week_correspondence_acknowledged_date_2"
        ).send_keys(TWELVE_WEEK_ACKNOWLEGED_DATE_YYYY)

        self.driver.find_element_by_name("twelve_week_correspondence_notes").send_keys(
            TWELVE_WEEK_CORRESPONDENCE_NOTES
        )
        self.driver.find_element_by_css_selector(
            "#id_twelve_week_response_state_0"
        ).click()
        self.driver.find_element_by_css_selector(
            "#id_twelve_week_correspondence_complete_date"
        ).click()

        self.driver.find_element_by_name("save").click()
        self.driver.find_element_by_link_text("Case").click()

        self.assertTrue(">View case</h1>" in self.driver.page_source)
        self.assertTrue("01/03/2021" in self.driver.page_source)
        self.assertTrue("01/07/2021" in self.driver.page_source)
        self.assertTrue(TWELVE_WEEK_CORRESPONDENCE_NOTES in self.driver.page_source)

    # def test_update_case_edit_final_decision(self):
    #     """Tests whether final decision can be updated"""
    #     self.driver.find_element_by_link_text("Edit final decision").click()

    #     self.assertTrue(">Final decision</h1>" in self.driver.page_source)

    #     self.driver.find_element_by_name("psb_progress_notes").send_keys(
    #         PSB_PROGRESS_NOTES
    #     )

    #     self.driver.find_element_by_name("retested_website_date_0").clear()
    #     self.driver.find_element_by_name("retested_website_date_0").send_keys(
    #         RETESTED_WEBSITE_DD
    #     )
    #     self.driver.find_element_by_name("retested_website_date_1").clear()
    #     self.driver.find_element_by_name("retested_website_date_1").send_keys(
    #         RETESTED_WEBSITE_MM
    #     )
    #     self.driver.find_element_by_name("retested_website_date_2").clear()
    #     self.driver.find_element_by_name("retested_website_date_2").send_keys(
    #         RETESTED_WEBSITE_YYYY
    #     )

    #     self.driver.find_element_by_css_selector(
    #         "#id_is_disproportionate_claimed_1"
    #     ).click()
    #     self.driver.find_element_by_name("disproportionate_notes").send_keys(
    #         DISPROPORTIONATE_NOTES
    #     )
    #     self.driver.find_element_by_css_selector(
    #         "#id_accessibility_statement_state_final_2"
    #     ).click()
    #     self.driver.find_element_by_name(
    #         "accessibility_statement_notes_final"
    #     ).send_keys(ACCESSIBILITY_STATEMENT_NOTES_FINAL)
    #     self.driver.find_element_by_css_selector(
    #         "#id_recommendation_for_enforcement_1"
    #     ).click()
    #     self.driver.find_element_by_name("recommendation_notes").send_keys(
    #         RECOMMENDATION_NOTES
    #     )

    #     self.driver.find_element_by_name("compliance_email_sent_date_0").clear()
    #     self.driver.find_element_by_name("compliance_email_sent_date_0").send_keys(
    #         COMPLIANCE_EMAIL_SENT_DATE_DD
    #     )
    #     self.driver.find_element_by_name("compliance_email_sent_date_1").clear()
    #     self.driver.find_element_by_name("compliance_email_sent_date_1").send_keys(
    #         COMPLIANCE_EMAIL_SENT_DATE_MM
    #     )
    #     self.driver.find_element_by_name("compliance_email_sent_date_2").clear()
    #     self.driver.find_element_by_name("compliance_email_sent_date_2").send_keys(
    #         COMPLIANCE_EMAIL_SENT_DATE_YYYY
    #     )

    #     self.driver.find_element_by_css_selector("#id_case_completed_1").click()
    #     self.driver.find_element_by_css_selector(
    #         "#id_final_decision_complete_date"
    #     ).click()

    #     self.driver.find_element_by_name("save").click()
    #     self.driver.find_element_by_link_text("Case").click()

    #     self.assertTrue(">View case</h1>" in self.driver.page_source)
    #     self.assertTrue("01/08/2021" in self.driver.page_source)
    #     self.assertTrue(DISPROPORTIONATE_NOTES in self.driver.page_source)
    #     self.assertTrue(ACCESSIBILITY_STATEMENT_NOTES_FINAL in self.driver.page_source)
    #     self.assertTrue(RECOMMENDATION_NOTES in self.driver.page_source)
    #     self.assertTrue("13/08/2021" in self.driver.page_source)

    def test_update_case_edit_enforcement_body_correspondence(self):
        """Tests whether enforcement body correspondence can be updated"""
        self.driver.find_element_by_link_text(
            "Edit equality body correspondence"
        ).click()

        self.assertTrue(
            ">Equality body correspondence</h1>" in self.driver.page_source
        )

        self.driver.find_element_by_name("psb_appeal_notes").send_keys(PSB_APPEAL_NOTES)

        self.driver.find_element_by_name("sent_to_enforcement_body_sent_date_0").clear()
        self.driver.find_element_by_name(
            "sent_to_enforcement_body_sent_date_0"
        ).send_keys(SENT_TO_ENFORCEMENT_BODY_SENT_DATE_DD)
        self.driver.find_element_by_name("sent_to_enforcement_body_sent_date_1").clear()
        self.driver.find_element_by_name(
            "sent_to_enforcement_body_sent_date_1"
        ).send_keys(SENT_TO_ENFORCEMENT_BODY_SENT_DATE_MM)
        self.driver.find_element_by_name("sent_to_enforcement_body_sent_date_2").clear()
        self.driver.find_element_by_name(
            "sent_to_enforcement_body_sent_date_2"
        ).send_keys(SENT_TO_ENFORCEMENT_BODY_SENT_DATE_YYYY)

        self.driver.find_element_by_css_selector("#id_enforcement_body_interested_1").click()
        self.driver.find_element_by_name(
            "enforcement_body_correspondence_notes"
        ).send_keys(ENFORCEMENT_BODY_CORRESPONDENCE_NOTES)
        self.driver.find_element_by_css_selector("#id_escalation_state_1").click()

        self.driver.find_element_by_css_selector(
            "#id_enforcement_correspondence_complete_date"
        ).click()

        self.driver.find_element_by_name("save").click()
        self.driver.find_element_by_link_text("Case").click()

        self.assertTrue(">View case</h1>" in self.driver.page_source)
        self.assertTrue(PSB_APPEAL_NOTES in self.driver.page_source)
        self.assertTrue("15/08/2021" in self.driver.page_source)
        self.assertTrue(
            ENFORCEMENT_BODY_CORRESPONDENCE_NOTES in self.driver.page_source
        )

    def test_update_case_edit_report_followup_dates(self):
        """Tests whether report followup dates can be updated"""
        self.driver.find_element_by_link_text("Edit report correspondence").click()
        self.assertTrue(
            ">Report correspondence</h1>" in self.driver.page_source
        )

        self.driver.find_element_by_link_text("Edit report followup due dates").click()
        self.assertTrue(
            ">Report followup dates</h1>" in self.driver.page_source
        )

        self.driver.find_element_by_name("report_followup_week_1_due_date_0").clear()
        self.driver.find_element_by_name("report_followup_week_1_due_date_0").send_keys(
            REPORT_FOLLOWUP_WEEK_1_DUE_DATE_DD
        )
        self.driver.find_element_by_name("report_followup_week_1_due_date_1").clear()
        self.driver.find_element_by_name("report_followup_week_1_due_date_1").send_keys(
            REPORT_FOLLOWUP_WEEK_1_DUE_DATE_MM
        )
        self.driver.find_element_by_name("report_followup_week_1_due_date_2").clear()
        self.driver.find_element_by_name("report_followup_week_1_due_date_2").send_keys(
            REPORT_FOLLOWUP_WEEK_1_DUE_DATE_YYYY
        )

        self.driver.find_element_by_name("report_followup_week_4_due_date_0").clear()
        self.driver.find_element_by_name("report_followup_week_4_due_date_0").send_keys(
            REPORT_FOLLOWUP_WEEK_4_DUE_DATE_DD
        )
        self.driver.find_element_by_name("report_followup_week_4_due_date_1").clear()
        self.driver.find_element_by_name("report_followup_week_4_due_date_1").send_keys(
            REPORT_FOLLOWUP_WEEK_4_DUE_DATE_MM
        )
        self.driver.find_element_by_name("report_followup_week_4_due_date_2").clear()
        self.driver.find_element_by_name("report_followup_week_4_due_date_2").send_keys(
            REPORT_FOLLOWUP_WEEK_4_DUE_DATE_YYYY
        )

        self.driver.find_element_by_name("report_followup_week_12_due_date_0").clear()
        self.driver.find_element_by_name(
            "report_followup_week_12_due_date_0"
        ).send_keys(REPORT_FOLLOWUP_WEEK_12_DUE_DATE_DD)
        self.driver.find_element_by_name("report_followup_week_12_due_date_1").clear()
        self.driver.find_element_by_name(
            "report_followup_week_12_due_date_1"
        ).send_keys(REPORT_FOLLOWUP_WEEK_12_DUE_DATE_MM)
        self.driver.find_element_by_name("report_followup_week_12_due_date_2").clear()
        self.driver.find_element_by_name(
            "report_followup_week_12_due_date_2"
        ).send_keys(REPORT_FOLLOWUP_WEEK_12_DUE_DATE_YYYY)

        self.driver.find_element_by_name("save_return").click()

        self.assertTrue(
            ">Report correspondence</h1>" in self.driver.page_source
        )

        self.assertTrue("Due 16/08/2021" in self.driver.page_source)
        self.assertTrue("Due 20/08/2021" in self.driver.page_source)
        self.assertTrue("Due 31/08/2021" in self.driver.page_source)

    def test_update_case_edit_twelve_week_correspondence_dates(self):
        """Tests whether 12 week correspondence dates can be updated"""
        self.driver.find_element_by_link_text("Edit 12 week correspondence").click()
        self.assertTrue(
            ">12 week correspondence</h1>" in self.driver.page_source
        )

        self.driver.find_element_by_link_text(
            "Edit 12 week correspondence due dates"
        ).click()
        self.assertTrue(
            ">12 week correspondence dates</h1>" in self.driver.page_source
        )

        self.driver.find_element_by_name("report_followup_week_12_due_date_0").clear()
        self.driver.find_element_by_name(
            "report_followup_week_12_due_date_0"
        ).send_keys(REPORT_FOLLOWUP_WEEK_12_DUE_DATE2_DD)
        self.driver.find_element_by_name("report_followup_week_12_due_date_1").clear()
        self.driver.find_element_by_name(
            "report_followup_week_12_due_date_1"
        ).send_keys(REPORT_FOLLOWUP_WEEK_12_DUE_DATE2_MM)
        self.driver.find_element_by_name("report_followup_week_12_due_date_2").clear()
        self.driver.find_element_by_name(
            "report_followup_week_12_due_date_2"
        ).send_keys(REPORT_FOLLOWUP_WEEK_12_DUE_DATE2_YYYY)

        self.driver.find_element_by_name("twelve_week_1_week_chaser_due_date_0").clear()
        self.driver.find_element_by_name(
            "twelve_week_1_week_chaser_due_date_0"
        ).send_keys(TWELVE_WEEK_1_WEEK_CHASER_DUE_DATE_DD)
        self.driver.find_element_by_name("twelve_week_1_week_chaser_due_date_1").clear()
        self.driver.find_element_by_name(
            "twelve_week_1_week_chaser_due_date_1"
        ).send_keys(TWELVE_WEEK_1_WEEK_CHASER_DUE_DATE_MM)
        self.driver.find_element_by_name("twelve_week_1_week_chaser_due_date_2").clear()
        self.driver.find_element_by_name(
            "twelve_week_1_week_chaser_due_date_2"
        ).send_keys(TWELVE_WEEK_1_WEEK_CHASER_DUE_DATE_YYYY)

        self.driver.find_element_by_name("twelve_week_4_week_chaser_due_date_0").clear()
        self.driver.find_element_by_name(
            "twelve_week_4_week_chaser_due_date_0"
        ).send_keys(TWELVE_WEEK_4_WEEK_CHASER_DUE_DATE_DD)
        self.driver.find_element_by_name("twelve_week_4_week_chaser_due_date_1").clear()
        self.driver.find_element_by_name(
            "twelve_week_4_week_chaser_due_date_1"
        ).send_keys(TWELVE_WEEK_4_WEEK_CHASER_DUE_DATE_MM)
        self.driver.find_element_by_name("twelve_week_4_week_chaser_due_date_2").clear()
        self.driver.find_element_by_name(
            "twelve_week_4_week_chaser_due_date_2"
        ).send_keys(TWELVE_WEEK_4_WEEK_CHASER_DUE_DATE_YYYY)

        self.driver.find_element_by_name("save_return").click()

        self.assertTrue(
            ">12 week correspondence</h1>" in self.driver.page_source
        )
        self.assertTrue("Due 13/07/2021" in self.driver.page_source)
        self.assertTrue("Due 20/07/2021" in self.driver.page_source)
        self.assertTrue("Due 24/07/2021" in self.driver.page_source)

    def test_update_case_edit_psb_is_unresponsive(self):
        """
        Tests whether unresponsive public sector bodies can be moved directly to enforcement body
        """
        self.driver.find_element_by_link_text("Edit report correspondence").click()
        self.assertTrue(
            ">Report correspondence</h1>" in self.driver.page_source
        )

        self.driver.find_element_by_link_text(
            "Unable to send report or no response from public sector body?"
        ).click()
        self.assertTrue(
            ">Public sector body is unresponsive</h1>"
            in self.driver.page_source
        )

        self.driver.find_element_by_css_selector("#id_no_psb_contact").click()

        self.driver.find_element_by_name("save_continue").click()

        self.assertTrue(
            ">Equality body correspondence</h1>" in self.driver.page_source
        )


class TestCaseDelete(TestCases):
    """
    Test case for integration tests of case deletion

    Methods
    -------
    setUp()
        Create case to delete
    test_delete_case()
        Tests whether case can be deleted
    test_restore_deleted_case()
        Tests whether deleted case can be restored
    """

    def setUp(self):
        """Create case to update"""
        super().setUp()
        self.driver.find_element_by_link_text("Create case").click()
        self.driver.find_element_by_name("organisation_name").send_keys(
            ORGANISATION_NAME_TO_DELETE
        )
        self.driver.find_element_by_name("home_page_url").send_keys(
            HOME_PAGE_URL_TO_DELETE
        )
        self.driver.find_element_by_css_selector(
            f"input[type='radio'][value='{ENFORCEMENT_BODY_VALUE}']"
        ).click()
        self.driver.find_element_by_name("save_exit").click()

    def test_delete_case(self):
        """Tests whether case can be deleted"""
        self.driver.find_element_by_link_text(ORGANISATION_NAME_TO_DELETE).click()
        self.driver.find_element_by_link_text("Delete case").click()
        self.assertTrue(">Delete case</h1>" in self.driver.page_source)

        self.driver.find_element_by_css_selector("#id_delete_reason_0").click()
        self.driver.find_element_by_name("delete_notes").send_keys(DELETE_NOTES)

        self.driver.find_element_by_name("delete").click()

        self.assertTrue(">Search</h1>" in self.driver.page_source)
        self.assertFalse(ORGANISATION_NAME_TO_DELETE in self.driver.page_source)

    def test_restore_deleted_case(self):
        """Tests whether deleted case can be restored"""
        self.driver.find_element_by_link_text("Search").click()
        self.assertFalse(ORGANISATION_NAME_TO_DELETE in self.driver.page_source)

        select = Select(self.driver.find_element_by_id("id_status"))
        select.select_by_visible_text("Deleted")
        self.driver.find_element_by_css_selector("input[type='submit']").click()

        self.assertTrue(ORGANISATION_NAME_TO_DELETE in self.driver.page_source)
        self.driver.find_element_by_link_text(ORGANISATION_NAME_TO_DELETE).click()

        self.assertTrue(">View case</h1>" in self.driver.page_source)
        self.assertTrue("deleted" in self.driver.page_source)

        self.driver.find_element_by_link_text("Restore").click()

        self.assertTrue(">View case</h1>" in self.driver.page_source)
        self.assertFalse("deleted" in self.driver.page_source)
