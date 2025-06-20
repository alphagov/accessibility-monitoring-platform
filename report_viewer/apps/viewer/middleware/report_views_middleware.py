"""report_views_middleware - logs views of the reports to the database"""

import hashlib
import logging
import re
from uuid import UUID

from django.http import HttpRequest

from accessibility_monitoring_platform.apps.common.models import UserCacheUniqueHash
from accessibility_monitoring_platform.apps.reports.models import ReportVisitsMetrics
from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report

logger = logging.getLogger(__name__)


class ReportMetrics:
    """Middleware for recording report views to the database"""

    def __init__(self, get_response):
        self.get_response = get_response

    def client_ip(self, request: HttpRequest) -> str:
        """Returns clients IP address

        Args:
            request (HttpRequest): Django request

        Returns:
            str: The clients IP address
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR", "")

    def user_fingerprint(self, request: HttpRequest) -> str:
        """
        Creates fingerprint to uniquely identify user.

        Args:
            request (HttpRequest): The Django request

        Returns:
            str: An amalgamated string of the user agent and client ip
        """
        return request.META.get("HTTP_USER_AGENT", "") + self.client_ip(request)

    def four_digit_hash(self, string_to_hash: str) -> int:
        """
        Hashes string to a unique four digit number

        The four digit number should be long enough to uniquely identify users on repeated visits
        but not long enough to reverse engineer.

        Args:
            string_to_hash (str): Any string

        Returns:
            int: The four digit hash of the input string
        """
        return (
            int(hashlib.sha256(string_to_hash.encode("utf-8")).hexdigest(), 16) % 10**4
        )

    def fingerprint_codename(self, fingerprint_hash: int) -> str:
        """Converts a number to a codename

        Args:
            fingerprint_hash (int): Any number

        Returns:
            str: A string containing multiple animal names
        """
        digit_to_animal_hash: list[str] = [
            "Owl",
            "Dog",
            "Cat",
            "Mongoose",
            "Chicken",
            "Ferret",
            "Rhino",
            "Horse",
            "Pig",
            "Yak",
        ]
        fingerprint_codename: str = ""
        for num in str(fingerprint_hash):
            fingerprint_codename += digit_to_animal_hash[int(num)]
        return fingerprint_codename

    def extract_guid_from_url(self, url: str) -> str | None:
        res = re.findall(
            "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", url
        )
        if len(res) == 1 and UUID(res[0], version=4):
            return res[0]
        return None

    def __call__(self, request):
        try:
            string_to_hash: str = self.user_fingerprint(request)
            fingerprint_hash: int = self.four_digit_hash(string_to_hash)
            if not UserCacheUniqueHash.objects.filter(
                fingerprint_hash=fingerprint_hash
            ).exists():
                absolute_uri: str = request.build_absolute_uri()
                guid: str | None = self.extract_guid_from_url(absolute_uri)
                if guid:
                    fingerprint_codename = self.fingerprint_codename(fingerprint_hash)
                    ReportVisitsMetrics(
                        base_case=S3Report.objects.get(guid=guid).base_case,
                        guid=guid,
                        fingerprint_hash=fingerprint_hash,
                        fingerprint_codename=fingerprint_codename,
                    ).save()
        except Exception as e:
            logger.warning("Error in ReportMetrics Middleware: %s", e)

        response = self.get_response(request)
        return response
