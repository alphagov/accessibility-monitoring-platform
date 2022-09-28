"""report_views_middleware - logs views of the reports to the database"""
import hashlib
from typing import List
from uuid import UUID

from django.http import HttpRequest

from report_viewer.settings.base import SECRET_KEY
from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report
from accessibility_monitoring_platform.apps.reports.models import ReportVisitsMetrics


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

    def user_fingerprint(self, request: HttpRequest, secret_key: str) -> str:
        """
        Creates fingerprint to uniquely identify user.

        The secret key is used as a salt for the hash.

        The salt makes it almost impossible to reverse engineer the hash and
        will also anonymise the hash after changing the secret key.

        Args:
            request (HttpRequest): The Django request
            secret_key (str): The instance's secret key

        Returns:
            str: An amalgamated string of the user agent, client ip, and secret key
        """
        return (
            request.META.get("HTTP_USER_AGENT", "")
            + self.client_ip(request)
            + secret_key
        )

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
            int(hashlib.sha256(string_to_hash.encode("utf-8")).hexdigest(), 16)
            % 10**4
        )

    def fingerprint_codename(self, fingerprint_hash: int) -> str:
        """Converts a number to a codename

        Args:
            fingerprint_hash (int): Any number

        Returns:
            str: A string containing multiple animal names
        """
        digit_to_animal_hash: List[str] = [
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

    def __call__(self, request):
        try:
            absolute_uri: str = request.build_absolute_uri()
            guid_index = -1
            if absolute_uri[-1] == "/":
                guid_index = -2

            guid: str = absolute_uri.split("/")[guid_index]
            if len(guid) == 36 and UUID(guid, version=4):
                string_to_hash = self.user_fingerprint(request, SECRET_KEY)
                fingerprint_hash = self.four_digit_hash(string_to_hash)
                fingerprint_codename = self.fingerprint_codename(fingerprint_hash)
                ReportVisitsMetrics(
                    case=S3Report.objects.get(guid=guid).case,
                    guid=guid,
                    fingerprint_hash=fingerprint_hash,
                    fingerprint_codename=fingerprint_codename,
                ).save()
        except Exception as e:  # pylint: disable=broad-except
            print(e)

        response = self.get_response(request)
        return response
