"""Populate websites"""
import requests

from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from accessibility_monitoring_platform.apps.cases.models import Case
from ...models import (
    Website,
    WEBSITE_RESPONSE_VALID,
    WEBSITE_RESPONSE_ERROR,
    WEBSITE_RESPONSE_OTHER,
)


class Command(BaseCommand):
    """Django command to reset the websites data"""

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """Reset websites data"""
        Website.objects.all().delete()
        cases: QuerySet[Case] = Case.objects.all()
        total_case: int = cases.count()
        for count, case in enumerate(cases[100:], start=1):
            print(f"[{count}/{total_case}] {case}")
            try:
                response: requests.Response = requests.get(case.home_page_url)
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
            except Exception as exception:
                Website.objects.create(
                    url=case.home_page_url,
                    response_type=WEBSITE_RESPONSE_ERROR,
                    response_content=str(exception),
                )
