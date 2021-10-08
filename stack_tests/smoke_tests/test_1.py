"""
Test template for integration tests
"""
import time
import unittest
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from dotenv import load_dotenv
# from selenium.webdriver.support.ui import Select
from app.parse_json import parse_integration_tests_json

settings = parse_integration_tests_json(settings_path='./stack_tests/smoke_tests_settings.json')

load_dotenv()

# ORGANISATION_NAME = "Example Organisation"
# HOME_PAGE_URL = "https://example.com"
# ENFORCEMENT_BODY_VALUE = "ehrc"
# ENFORCEMENT_BODY_LABEL = "Equality and Human Rights Commission"
# SERVICE_NAME = "Service name"
# ZENDESK_URL = "https://zendesk.com"
# TRELLO_URL = "https://trello.com"
# CASE_DETAILS_NOTES = """I am
# a multiline
# case details note, I am"""

# CONTACT_FIRST_NAME = "Contact first name"
# CONTACT_LAST_NAME = "Contact last name"
# CONTACT_JOB_TITLE = "Contact title"
# EMAIL = "contact_email@example.com"
# CONTACT_NOTES = """I am
# a multiline
# contact note, I am"""

# TEST_RESULTS_URL = "https://test-results.com"
# ACCESSIBILITY_STATEMENT_STATUS = "missing"
# ACCESSIBILITY_STATEMENT_NOTES = """I am
# a multiline
# accessibility statement note, I am"""
# WEBSITE_COMPLIANCE_NOTES = """I am
# a multiline
# accessibility statement note, I am"""


# REPORT_DRAFT_URL = "https://report-draft.com"
# REPORT_REVIEWER_NOTES = """I am
# a multiline
# report reviewer note, I am"""
# REPORT_FINAL_PDF_URL = "https://report-final-pdf.com"
# REPORT_FINAL_ODT_URL = "https://report-final-odt.com"

# REPORT_SENT_DATE_DD = "31"
# REPORT_SENT_DATE_MM = "12"
# REPORT_SENT_DATE_YYYY = "2020"
# REPORT_ACKNOWLEGED_DATE_DD = "1"
# REPORT_ACKNOWLEGED_DATE_MM = "4"
# REPORT_ACKNOWLEGED_DATE_YYYY = "2021"
# REPORT_CORRESPONDENCE_NOTES = """I am
# a multiline
# report correspondence note, I am"""

# TWELVE_WEEK_UPDATE_REQUESTED_DD = "1"
# TWELVE_WEEK_UPDATE_REQUESTED_MM = "3"
# TWELVE_WEEK_UPDATE_REQUESTED_YYYY = "2021"
# TWELVE_WEEK_ACKNOWLEGED_DATE_DD = "1"
# TWELVE_WEEK_ACKNOWLEGED_DATE_MM = "7"
# TWELVE_WEEK_ACKNOWLEGED_DATE_YYYY = "2021"
# TWELVE_WEEK_CORRESPONDENCE_NOTES = """I am
# a multiline
# 12 week correspondence note, I am"""

# PSB_PROGRESS_NOTES = """I am
# a multiline
# public sector body progress note, I am"""
# RETESTED_WEBSITE_DD = "1"
# RETESTED_WEBSITE_MM = "8"
# RETESTED_WEBSITE_YYYY = "2021"
# DISPROPORTIONATE_NOTES = """I am
# a multiline
# disproportionate burden note, I am"""
# ACCESSIBILITY_STATEMENT_NOTES_FINAL = """I am
# a multiline
# accessibility statement final note, I am"""
# RECOMMENDATION_NOTES = """I am
# a multiline
# recommendation note, I am"""
# COMPLIANCE_EMAIL_SENT_DATE_DD = "13"
# COMPLIANCE_EMAIL_SENT_DATE_MM = "8"
# COMPLIANCE_EMAIL_SENT_DATE_YYYY = "2021"

# PSB_APPEAL_NOTES = """I am
# a multiline
# public sector body appeal note, I am"""
# SENT_TO_ENFORCEMENT_BODY_SENT_DATE_DD = "15"
# SENT_TO_ENFORCEMENT_BODY_SENT_DATE_MM = "8"
# SENT_TO_ENFORCEMENT_BODY_SENT_DATE_YYYY = "2021"
# ENFORCEMENT_BODY_CORRESPONDENCE_NOTES = """I am
# a multiline
# enforcement body correspondence note, I am"""

# REPORT_FOLLOWUP_WEEK_1_DUE_DATE_DD = "16"
# REPORT_FOLLOWUP_WEEK_1_DUE_DATE_MM = "8"
# REPORT_FOLLOWUP_WEEK_1_DUE_DATE_YYYY = "2021"
# REPORT_FOLLOWUP_WEEK_4_DUE_DATE_DD = "20"
# REPORT_FOLLOWUP_WEEK_4_DUE_DATE_MM = "8"
# REPORT_FOLLOWUP_WEEK_4_DUE_DATE_YYYY = "2021"
# REPORT_FOLLOWUP_WEEK_12_DUE_DATE_DD = "31"
# REPORT_FOLLOWUP_WEEK_12_DUE_DATE_MM = "8"
# REPORT_FOLLOWUP_WEEK_12_DUE_DATE_YYYY = "2021"

# REPORT_FOLLOWUP_WEEK_12_DUE_DATE2_DD = "13"
# REPORT_FOLLOWUP_WEEK_12_DUE_DATE2_MM = "7"
# REPORT_FOLLOWUP_WEEK_12_DUE_DATE2_YYYY = "2021"
# TWELVE_WEEK_1_WEEK_CHASER_DUE_DATE_DD = "20"
# TWELVE_WEEK_1_WEEK_CHASER_DUE_DATE_MM = "7"
# TWELVE_WEEK_1_WEEK_CHASER_DUE_DATE_YYYY = "2021"
# TWELVE_WEEK_4_WEEK_CHASER_DUE_DATE_DD = "24"
# TWELVE_WEEK_4_WEEK_CHASER_DUE_DATE_MM = "7"
# TWELVE_WEEK_4_WEEK_CHASER_DUE_DATE_YYYY = "2021"

# DELETE_NOTES = """I am
# a multiline
# deletion note, I am"""

# ORGANISATION_NAME_TO_DELETE = "Example Organisation to Delete"
# HOME_PAGE_URL_TO_DELETE = "https://example-to-delete.com"


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
        print(settings["testing_endpoint"])
        self.driver.get(f"""{settings["testing_endpoint"]}accounts/login/?next=/""")
        self.driver.find_element_by_name("username").send_keys(
            os.getenv("SMOKE_TESTS_USERNAME")
        )
        self.driver.find_element_by_name("password").send_keys(
            os.getenv("SMOKE_TESTS_PASSWORD")
        )
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

class TestDashboard(SeleniumTest):
    """
    Test case for integration tests of dashboard

    Methods
    -------
    test_dashboard()
        Tests whether users can access the dashboard
    """

    def test_dashboard(self):
        """Tests whether user can login"""
        self.login()
        self.driver.find_element_by_xpath('//input[@value="View all cases"]').click()
        self.assertEqual(
            '<h1 class="govuk-heading-xl">All cases</h1>' in self.driver.page_source,
            True,
        )
        self.driver.find_element_by_xpath('//input[@value="View your cases"]').click()
        self.assertEqual(
            '<h1 class="govuk-heading-xl">Your cases</h1>' in self.driver.page_source,
            True,
        )


class TestSearch(SeleniumTest):
    """
    Test case for integration tests of search

    Methods
    -------
    test_search()
        Tests whether users can access the dashboard
    """

    def test_search(self):
        """Tests whether user can login"""
        self.login()
        # self.driver.find_element_by_xpath('//input[@value="View all cases"]').click()
        self.driver.find_element_by_link_text("Search").click()
        self.assertEqual(
            '<h1 class="govuk-heading-xl">Search</h1>' in self.driver.page_source,
            True,
        )
        self.driver.find_element_by_name("search").send_keys("1")
        self.driver.find_element_by_xpath('//input[@value="Search"]').click()
        self.assertEqual(
            '<h1 class="govuk-heading-xl">Search</h1>' in self.driver.page_source,
            True,
        )

class TestAccountDetails(SeleniumTest):
    """
    Test case for integration tests of AccountDetails

    Methods
    -------
    test_search()
        Tests whether users can access the dashboard
    """

    def test_search(self):
        """Tests whether user can login"""
        self.login()
        # self.driver.find_element_by_xpath('//input[@value="View all cases"]').click()
        self.driver.find_element_by_link_text("Search").click()
        self.assertEqual(
            '<h1 class="govuk-heading-xl">Search</h1>' in self.driver.page_source,
            True,
        )
        # self.driver.find_element_by_name("search").send_keys("1")
        # self.driver.find_element_by_xpath('//input[@value="Search"]').click()
        # self.assertEqual(
        #     '<h1 class="govuk-heading-xl">Search</h1>' in self.driver.page_source,
        #     True,
        # )