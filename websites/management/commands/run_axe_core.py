"""Populate websites"""
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

from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from ...models import (
    Website,
    WEBSITE_RESPONSE_VALID,
    WEBSITE_RESPONSE_ERROR,
    WEBSITE_RESPONSE_OTHER,
    WEBSITE_WEBDRIVER_ERROR,
)

REQUEST_HEADERS: Dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
}


def get_url(url: str):
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
        Website.objects.create(
            url=url,
            response_status_code=response.status_code,
            type=response_type,
            response_headers=str(response.headers),
            response_content=response.content,
        )
    except Exception as exception:  # pylint: disable=broad-except
        Website.objects.create(
            url=url,
            type=WEBSITE_RESPONSE_ERROR,
            response_content=str(exception),
        )


def get_urls(urls: List[str]):
    """Get urls using requests library"""
    number_of_urls: int = len(urls)
    for count, url in enumerate(urls, start=1):
        print(f"[{count}/{number_of_urls}] {url}")
        get_url(url=url)


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


def run_axe_core():
    """Run axe-core tests"""
    websites: QuerySet[Website] = Website.objects.all()
    chrome_options: Options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}

    total_websites: int = websites.count()
    for count, website in enumerate(websites, start=1):
        print(f"[{count}/{total_websites}] {website}")
        if website.results:
            continue
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=chrome_options,
        )
        try:
            driver.get(website.url)
            axe: Axe = Axe(driver)
            axe.inject()
            axe_core_results: Dict = axe.run()
            record_axe_results(website=website, axe_core_results=axe_core_results)
            driver.close()
        except WebDriverException as exception:
            website.type = WEBSITE_WEBDRIVER_ERROR
            website.response_content = str(exception)
            website.save()


class Command(BaseCommand):
    """Django command to reset the websites data and run axe-core tests"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--initial",
            action="store_true",
            dest="initial",
            default=False,
            help="Initialise data",
        )
        parser.add_argument(
            "--file",
            action="store",
            dest="file",
            default=False,
            help="Read URLs from file",
        )

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """Run axe-core tests"""
        initial = options["initial"]
        url_file = options["file"]
        urls: List[str] = []

        if url_file:
            with open(url_file, "r", encoding="utf-8") as f:
                urls: List[str] = [url.strip() for url in f.readlines()]

        if initial:
            Website.objects.all().delete()

        if urls:
            get_urls(urls=urls)

        run_axe_core()
