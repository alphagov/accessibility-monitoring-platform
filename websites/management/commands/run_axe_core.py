"""Populate websites"""
# pylint: disable=line-too-long
import json
import requests
from typing import Dict, List

from axe_selenium_python import Axe
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from accessibility_monitoring_platform.apps.cases.models import Case
from ...models import (
    Website,
    WEBSITE_RESPONSE_VALID,
    WEBSITE_RESPONSE_ERROR,
    WEBSITE_RESPONSE_OTHER,
)

REQUEST_HEADERS: Dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
}


def reset_websites():
    """Reset websites data using requests library"""
    Website.objects.all().delete()
    cases: QuerySet[Case] = Case.objects.all()
    total_case: int = cases.count()
    for count, case in enumerate(cases, start=1):
        print(f"[{count}/{total_case}] {case}")
        if case.home_page_url == "":
            break
        try:
            response: requests.Response = requests.get(
                case.home_page_url, headers=REQUEST_HEADERS, timeout=5
            )
            response_type: str = (
                WEBSITE_RESPONSE_VALID
                if response.status_code == 200
                else WEBSITE_RESPONSE_OTHER
            )
            Website.objects.create(
                url=case.home_page_url,
                response_status_code=response.status_code,
                response_type=response_type,
                response_headers=str(response.headers),
                response_content=response.content,
            )
        except Exception as exception:  # pylint: disable=broad-except
            Website.objects.create(
                url=case.home_page_url,
                response_type=WEBSITE_RESPONSE_ERROR,
                response_content=str(exception),
            )


def record_axe_results(website: Website, axe_core_results: Dict):
    """Count numbers of critical and serious Axe errors"""
    violations: List[Dict] = []
    website.axe_core_results = json.dumps(axe_core_results)

    if "error" in axe_core_results:
        website.axe_core_message = f"Error: {axe_core_results['error']['message']}"
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

        website.axe_core_critical_count = axe_core_critical_count
        website.axe_core_serious_count = axe_core_serious_count
        website.axe_core_violations = json.dumps(violations)
        website.axe_core_message = "Successful test"

    website.save()


def run_axe_core():
    """Run axe-core tests"""
    websites: QuerySet[Website] = Website.objects.all()

    total_websites: int = websites.count()
    for count, website in enumerate(websites, start=1):
        print(f"[{count}/{total_websites}] {website}")
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install())
        )
        driver.get(website.url)
        axe: Axe = Axe(driver)
        axe.inject()
        axe_core_results: Dict = axe.run()
        record_axe_results(website=website, axe_core_results=axe_core_results)
        driver.close()


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

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """Run axe-core tests"""
        initial = options["initial"]

        if initial:
            reset_websites()

        run_axe_core()
