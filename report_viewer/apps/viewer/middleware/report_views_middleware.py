"""report_views_middleware - logs views of the reports to the database"""
import hashlib
from uuid import UUID
from report_viewer.settings.base import SECRET_KEY
from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report
from accessibility_monitoring_platform.apps.reports.models import ReportVisitsMetrics


class ReportMetrics:
    """Middle for recording report views to the database"""

    digit_to_animal_hash = [
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

    def __init__(self, get_response):
        self.get_response = get_response

    def client_ip(self, request) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")

    def string_to_hash(self, request, secret_key: str) -> str:
        return (
            request.META.get("HTTP_USER_AGENT", "")
            + self.client_ip(request)
            + secret_key
        )

    def fingerprint_hash(self, string_to_hash: str) -> int:
        return (
            int(hashlib.sha256(string_to_hash.encode("utf-8")).hexdigest(), 16)
            % 10**4
        )

    def fingerprint_codename(self, fingerprint_hash: int) -> str:
        fingerprint_codename: str = ""
        for num in str(fingerprint_hash):
            fingerprint_codename += self.digit_to_animal_hash[int(num)]
        return fingerprint_codename

    def __call__(self, request):
        try:
            absolute_uri: str = request.build_absolute_uri()
            guid_index = -1
            if absolute_uri[-1] == "/":
                guid_index = -2

            guid: str = absolute_uri.split("/")[guid_index]
            if len(guid) == 36 and UUID(guid, version=4):
                string_to_hash = self.string_to_hash(request, SECRET_KEY)
                fingerprint_hash = self.fingerprint_hash(string_to_hash)
                fingerprint_codename = self.fingerprint_codename(fingerprint_hash)
                ReportVisitsMetrics(
                    case=S3Report.objects.get(guid=guid).case,
                    guid=guid,
                    fingerprint_hash=fingerprint_hash,
                    fingerprint_codename=fingerprint_codename,
                ).save()
        except Exception as e:
            print(e)

        response = self.get_response(request)
        return response
