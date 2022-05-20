import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
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


class TestHomepage(SeleniumTest):
    """
    Test case for integration tests of report viewer
    Methods
    -------
    test_404_displays_correctly()
        Tests whether user can see 404 page
    """

    def test_404_displays_correctly(self):
        self.driver.get(f"""{settings["testing_endpoint"]}""")
        self.assertEqual(
            "Page not found" in self.driver.page_source,
            True,
        )
        self.assertEqual(
            "If you entered a web address, check it is correct."
            in self.driver.page_source,
            True,
        )
