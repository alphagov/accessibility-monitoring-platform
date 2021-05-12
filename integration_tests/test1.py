import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class TestSum(unittest.TestCase):

    def test_login_page_renders(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome("./integration_tests/chromedriver", chrome_options=options)
        driver.get("http://localhost:8000/accounts/login/?next=/")
        self.assertEqual("Accessiblity Monitoring Platform" in driver.page_source, True)
