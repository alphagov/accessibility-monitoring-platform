"""Populate websites"""
# pylint: disable=line-too-long
from typing import List

from selenium.webdriver.chrome.options import Options

from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from ...models import Website
from ...utils import create_website, axe_check_website, get_chrome_options


def create_websites(urls: List[str]):
    """Create websites from urls"""
    for url in urls:
        create_website(url=url)


def run_axe_core():
    """Run axe-core tests"""
    websites: QuerySet[Website] = Website.objects.filter(results="")
    chrome_options: Options = get_chrome_options()

    for website in websites:
        axe_check_website(website, chrome_options)


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
            create_websites(urls=urls)

        run_axe_core()
