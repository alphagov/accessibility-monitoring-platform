"""Populate websites"""
# pylint: disable=line-too-long
import requests
from typing import Dict

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


class Command(BaseCommand):
    """Django command to reset the websites data"""

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """Reset websites data"""
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
