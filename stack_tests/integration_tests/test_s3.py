import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import Select
from app.parse_json import parse_integration_tests_json
import argparse
import re
import time


parser = argparse.ArgumentParser(description="Settings for integration tests")

parser.add_argument(
    "-s" "--settings-json", dest="settings_json", help="Path for json settings"
)

args = parser.parse_args()

settings = parse_integration_tests_json(settings_path=args.settings_json)

ORGANISATION_NAME = "Example Organisation2"
HOME_PAGE_URL = "https://exampleTwo.com"
ENFORCEMENT_BODY_VALUE = "ehrc"


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
            options=options,
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

class TestS3ReportCreation(TestCases):
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

    def test_load_guid_attached_to_case(self):
        """Tests whether case can be created"""
        self.driver.get("http://localhost:8001/cases/")
        number_of_cases: int = self.driver.page_source.count("govuk-heading-m cases-sub-heading")
        self.driver.get(f"http://localhost:8001/report/save/{number_of_cases}")
        html = self.driver.page_source
        res = re.findall(r"\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b", html)
        self.assertTrue(len(res) == 1)

        self.driver.get(f"http://localhost:8001/report/{res[0]}")

        self.assertEqual(
            f'org: {ORGANISATION_NAME}' in self.driver.page_source,
            True,
        )
