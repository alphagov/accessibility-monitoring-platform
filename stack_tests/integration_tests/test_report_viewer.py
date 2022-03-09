import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from app.parse_json import parse_integration_tests_json
import argparse
import re


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

    # def login(self):
    #     """Login in to platform"""
    #     self.driver.get("http://localhost:8002/accounts/login/?next=/")
    #     self.driver.find_element_by_name("username").send_keys("admin@email.com")
    #     self.driver.find_element_by_name("password").send_keys("secret")
    #     self.driver.find_element_by_xpath('//input[@value="Submit"]').click()


class TestHomepage(SeleniumTest):
    """
    Test case for integration tests of report viewer

    Methods
    -------
    test_homepage_displays_correctly()
        Tests whether user can see homepage
    """

    def test_homepage_displays_correctly(self):
        self.driver.get("http://localhost:8002/")
        self.assertEqual(
            'This is the homepage of the report viewer' in self.driver.page_source,
            True,
        )
