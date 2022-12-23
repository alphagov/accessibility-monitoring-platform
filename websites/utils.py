"""Utility functions for websites app"""
# pylint: disable=line-too-long
import json
import requests
from typing import Dict, List

from axe_selenium_python import Axe
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from .models import (
    Website,
    WEBSITE_RESPONSE_VALID,
    WEBSITE_RESPONSE_ERROR,
    WEBSITE_RESPONSE_OTHER,
    WEBSITE_WEBDRIVER_ERROR,
)

REQUEST_HEADERS: Dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
}


def create_website(url: str):
    """Get URL and store response"""
    try:
        response: requests.Response = requests.get(
            url, headers=REQUEST_HEADERS, timeout=5
        )
        response_type: str = (
            WEBSITE_RESPONSE_VALID
            if response.status_code == 200
            else WEBSITE_RESPONSE_OTHER
        )
        website: Website = Website.objects.create(
            url=url,
            response_status_code=response.status_code,
            type=response_type,
            response_headers=str(response.headers),
            response_content=response.content,
        )
    except Exception as exception:  # pylint: disable=broad-except
        website: Website = Website.objects.create(
            url=url,
            type=WEBSITE_RESPONSE_ERROR,
            response_content=str(exception),
        )
    print(f"Created {website}")


def record_axe_results(website: Website, axe_core_results: Dict):
    """Count numbers of critical and serious Axe errors"""
    violations: List[Dict] = []
    website.results = json.dumps(axe_core_results)

    if "error" in axe_core_results:
        website.message = f"Error: {axe_core_results['error']['message']}"
    else:
        axe_core_critical_count = 0
        axe_core_serious_count = 0

        for violation in axe_core_results["violations"]:
            if violation["impact"] == "critical":
                axe_core_critical_count += 1
                violations.append(violation)
            elif violation["impact"] == "serious":
                axe_core_serious_count += 1
                violations.append(violation)

        website.critical = axe_core_critical_count
        website.serious = axe_core_serious_count
        website.violations = json.dumps(violations)
        website.message = "Successful test"

    website.save()


def axe_check_website(website: Website, chrome_options: Options):
    """Run Axe core checks on a website"""
    print(f"Axe check started {website}")

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=chrome_options,
    )
    try:
        driver.get(website.url)
        website.final_url = driver.current_url
        axe: Axe = Axe(driver)
        axe.inject()
        axe_core_results: Dict = axe.run()
        record_axe_results(website=website, axe_core_results=axe_core_results)
        driver.close()
    except WebDriverException as exception:
        website.type = WEBSITE_WEBDRIVER_ERROR
        website.response_content = str(exception)
        website.save()

    print(f"Axe check finished {website}")


def get_chrome_options() -> Options:
    """Return options for chrome webdriver"""
    chrome_options: Options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    return chrome_options
