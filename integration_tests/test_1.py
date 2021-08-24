"""
Test template for integration tests
"""

import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver

ORGANISATION_NAME = "Example Organisation"
HOME_PAGE_URL = "https://example.com"
SERVICE_NAME = "Service name"
EMAIL = "contact_email@example.com"
ACCESSIBILITY_STATEMENT_NOTES = """I am
a multiline
accessibility statement note, I am"""


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
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        self.driver: WebDriver = webdriver.Chrome(
            executable_path="./integration_tests/chromedriver", chrome_options=options
        )

    def login(self):
        """Login in to platform"""
        self.driver.get("http://localhost:8001/accounts/login/?next=/")
        username_input = self.driver.find_element_by_name("username")
        username_input.send_keys("admin@email.com")
        password_input = self.driver.find_element_by_name("password")
        password_input.send_keys("secret")
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
    Test case for integration tests of case create and update

    Methods
    -------
    setUp()
        Login and navigate to Cases list
    test_create_case()
        Tests whether case can be created
    test_duplicate_case_found()
        Tests whether duplicate case is found
    test_update_case()
        Tests whether case can be updated
    """

    def setUp(self):
        """Setup selenium test environment; Login and navigate to Cases list"""
        super().setUp()
        self.login()
        self.driver.find_element_by_link_text("Cases").click()

    def test_create_case(self):
        """Tests whether case can be created"""
        self.driver.find_element_by_link_text("Create case").click()
        organisation_name_input = self.driver.find_element_by_name("organisation_name")
        organisation_name_input.send_keys(ORGANISATION_NAME)
        home_page_url_input = self.driver.find_element_by_name("home_page_url")
        home_page_url_input.send_keys(HOME_PAGE_URL)
        self.driver.find_element_by_name("save_exit").click()
        self.assertTrue(
            '<h1 class="govuk-heading-xl">Cases</h1>' in self.driver.page_source
        )
        self.assertTrue(ORGANISATION_NAME in self.driver.page_source)

    def test_duplicate_case_found(self):
        """Tests whether duplicate case is found"""
        self.driver.find_element_by_link_text("Create case").click()
        organisation_name_input = self.driver.find_element_by_name("organisation_name")
        organisation_name_input.send_keys(ORGANISATION_NAME)
        home_page_url_input = self.driver.find_element_by_name("home_page_url")
        home_page_url_input.send_keys(HOME_PAGE_URL)
        self.driver.find_element_by_name("save_exit").click()
        self.assertTrue(
            '<h1 class="govuk-heading-xl">Create case</h1>' in self.driver.page_source
        )
        self.assertTrue(
            "We have found 1 cases matching the details you have given"
            in self.driver.page_source
        )

    def test_update_case(self):
        """Tests whether case can be updated"""
        self.driver.find_element_by_link_text(ORGANISATION_NAME).click()
        self.assertTrue(">View case</h1>" in self.driver.page_source)
        self.driver.find_element_by_link_text("Edit case details").click()

        self.assertTrue(">Edit case | Case details</h1>" in self.driver.page_source)
        service_name_input = self.driver.find_element_by_name("service_name")
        service_name_input.send_keys(SERVICE_NAME)
        self.driver.find_element_by_css_selector(
            "input[type='radio'][value='ehrc']"
        ).click()
        self.driver.find_element_by_name("save_continue").click()

        self.assertTrue(">Edit case | Contact details</h1>" in self.driver.page_source)
        self.driver.find_element_by_xpath('//input[@value="Create contact"]').click()
        service_name_input = self.driver.find_element_by_name("form-0-email")
        service_name_input.send_keys(EMAIL)
        self.driver.find_element_by_name("save_continue").click()

        self.assertTrue(">Edit case | Testing details</h1>" in self.driver.page_source)
        service_name_textarea = self.driver.find_element_by_name(
            "accessibility_statement_notes"
        )
        service_name_textarea.send_keys(ACCESSIBILITY_STATEMENT_NOTES)
        self.driver.find_element_by_name("save_continue").click()

        self.assertTrue(">Edit case | Report details</h1>" in self.driver.page_source)
        self.driver.find_element_by_name("save_continue").click()

        self.assertTrue(
            ">Edit case | Report correspondence</h1>" in self.driver.page_source
        )
        self.driver.find_element_by_name("save_continue").click()

        self.assertTrue(
            ">Edit case | 12 week correspondence</h1>" in self.driver.page_source
        )
        self.driver.find_element_by_name("save_continue").click()

        self.assertTrue(">Edit case | Final decision</h1>" in self.driver.page_source)
        self.driver.find_element_by_name("save_continue").click()

        self.assertTrue(
            ">Edit case | Equality body correspondence</h1>" in self.driver.page_source
        )
        self.driver.find_element_by_name("save_exit").click()

        self.assertTrue(">View case</h1>" in self.driver.page_source)
        self.assertTrue(SERVICE_NAME in self.driver.page_source)
        self.assertTrue(
            "Equality and Human Rights Commission" in self.driver.page_source
        )
        self.assertTrue(EMAIL in self.driver.page_source)
        self.assertTrue(ACCESSIBILITY_STATEMENT_NOTES in self.driver.page_source)
