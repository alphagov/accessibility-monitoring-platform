"""
Test template for integration tests
"""
import unittest
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

from dotenv import load_dotenv
from app.parse_json import parse_integration_tests_json
import argparse

parser = argparse.ArgumentParser(description="Settings for integration tests")

parser.add_argument(
    "-s" "--settings-json", dest="settings_json", help="Path for json settings"
)

args = parser.parse_args()

settings = parse_integration_tests_json(settings_path=args.settings_json)


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

    settings = ""

    def setUp(self):
        """Setup selenium test environment"""
        options: Options = Options()
        if settings["headless"]:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        self.driver: WebDriver = webdriver.Chrome(
            executable_path=ChromeDriverManager().install(),
            options=options,
        )

    def login(self):
        """Login in to platform"""
        load_dotenv()
        if (
            os.getenv("SMOKE_TESTS_USERNAME") is None
            or os.getenv("SMOKE_TESTS_PASSWORD") is None
            or os.getenv("SMOKE_TESTS_USERNAME") == ""
            or os.getenv("SMOKE_TESTS_PASSWORD") == ""
        ):
            raise Exception(
                "Missing SMOKE_TESTS_USERNAME and SMOKE_TESTS_PASSWORD from .env"
            )

        self.driver.get(f"""{settings["testing_endpoint"]}account/login/?next=/""")
        self.driver.find_element_by_name("auth-username").send_keys(
            os.getenv("SMOKE_TESTS_USERNAME")
        )
        self.driver.find_element_by_name("auth-password").send_keys(
            os.getenv("SMOKE_TESTS_PASSWORD")
        )
        self.driver.find_element_by_name("auth-password").send_keys(Keys.RETURN)


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
            """<h1 class="govuk-heading-xl">Your cases</h1>"""
            in self.driver.page_source,
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
        self.driver.find_element_by_xpath(
            """//input[@value="View all cases"]"""
        ).click()
        self.assertEqual(
            """<h1 class="govuk-heading-xl">All cases</h1>"""
            in self.driver.page_source,
            True,
        )
        self.driver.find_element_by_xpath(
            """//input[@value="View your cases"]"""
        ).click()
        self.assertEqual(
            """<h1 class="govuk-heading-xl">Your cases</h1>"""
            in self.driver.page_source,
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
        # self.driver.find_element_by_xpath("//input[@value="View all cases"]").click()
        self.driver.find_element_by_link_text("Search").click()
        self.assertEqual(
            """<h1 class="govuk-heading-xl">Search</h1>""" in self.driver.page_source,
            True,
        )
        self.driver.find_element_by_name("search").send_keys("1")
        self.driver.find_element_by_xpath("""//input[@value="Search"]""").click()
        self.assertEqual(
            """<h1 class="govuk-heading-xl">Search</h1>""" in self.driver.page_source,
            True,
        )
        self.driver.find_element_by_link_text("Next").click()
        self.assertEqual(
            """<h1 class="govuk-heading-xl">Search</h1>""" in self.driver.page_source,
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
        # self.driver.find_element_by_xpath("//input[@value="View all cases"]").click()
        self.driver.find_element_by_link_text("Settings").click()
        self.assertEqual(
            """<h1 class="govuk-heading-xl">Account details</h1>"""
            in self.driver.page_source,
            True,
        )


class TestCaseView(SeleniumTest):
    """
    Test case for integration tests of Case view

    Methods
    -------
    test_case_view()
        Tests whether users can access case view
    """

    def test_case_view(self):
        """Tests whether user can view cases"""
        self.login()
        self.driver.find_element_by_link_text("Search").click()

        self.driver.find_element_by_name("search").send_keys("Met Office")

        self.driver.find_element_by_name("search").send_keys(Keys.RETURN)
        self.driver.find_element_by_link_text("Met Office").click()
        self.assertEqual("View case" in self.driver.page_source, True)

        pages_to_test = [
            ("Edit case details", "Case details"),
            ("Edit testing details", "Testing details"),
            ("Edit report details", "Report details"),
            ("Edit QA process", "QA process"),
            ("Edit contact details", "Contact details"),
            ("Edit report correspondence", "Report correspondence"),
            ("Edit 12-week correspondence", "12-week correspondence"),
            ("Edit reviewing changes", "Reviewing changes"),
            (
                "Edit final accessibility statement compliance decision",
                "Final accessibility statement compliance decision",
            ),
            (
                "Edit final website compliance decision",
                "Final website compliance decision",
            ),
            ("Edit closing the case", "Closing the case"),
            ("Edit post case summary", "Post case summary"),
            ("Edit equality body summary", "Equality body summary"),
        ]

        for page in pages_to_test:
            self.driver.find_element_by_link_text(page[0]).click()
            self.assertEqual(page[1] in self.driver.page_source, True)
            self.driver.back()
