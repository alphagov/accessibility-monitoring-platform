import hashlib
from uuid import UUID
from report_viewer.settings.base import SECRET_KEY
from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report

class SimpleMiddleware:
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

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")

    def __call__(self, request):
        absolute_uri: str = request.build_absolute_uri()
        if "/" in absolute_uri:
            guid: str = absolute_uri.split("/")[-1]
            if len(guid) == 36 and UUID(guid, version=4):
                s3_report: S3Report = S3Report.objects.get(guid=guid)

                string_to_hash: str = (
                    request.META.get("HTTP_USER_AGENT", "")
                    + self.get_client_ip(request=request)
                    + SECRET_KEY
                )
                four_digit_hash: int = int(
                    hashlib.sha256(string_to_hash.encode("utf-8")).hexdigest(), 16
                ) % 10**4

                fingerprint_codename: str = ""
                for num in str(four_digit_hash):
                    fingerprint_codename += self.digit_to_animal_hash[int(num)]

                print(fingerprint_codename)

        response = self.get_response(request)
        return response
