"""
Test template for integration tests
"""

import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver


class TestSum(unittest.TestCase):
    """
    Test case for integration tests

    Methods
    -------
    test_login_page_renders()
        Tests whether login page correctly renders
    """

    def test_login_page_renders(self):
        """ Tests whether login page correctly renders """
        options: Options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver: WebDriver = webdriver.Chrome(
            executable_path="./integration_tests/chromedriver",
            chrome_options=options
        )
        driver.get(url="http://localhost:8001/accounts/login/?next=/")

        self.assertEqual("Accessiblity Monitoring Platform" in driver.page_source, True)
