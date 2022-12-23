"""Models for recording results of bulk testing of websites"""
from typing import List, Tuple
from django.db import models


WEBSITE_RESPONSE_VALID: str = "200"
WEBSITE_RESPONSE_ERROR: str = "error"
WEBSITE_RESPONSE_OTHER: str = "other"
WEBSITE_WEBDRIVER_ERROR: str = "webdriver"
WEBSITE_RESPONSE_CHOICES: List[Tuple[str, str]] = [
    (WEBSITE_RESPONSE_VALID, "Valid"),
    (WEBSITE_RESPONSE_ERROR, "Error"),
    (WEBSITE_WEBDRIVER_ERROR, "Webdriver error"),
    (WEBSITE_RESPONSE_OTHER, "Other"),
]


class Website(models.Model):
    """Websites tested for accessibility"""

    url = models.TextField(default="", blank=True)
    final_url = models.TextField(default="", blank=True)
    type = models.CharField(
        max_length=10, choices=WEBSITE_RESPONSE_CHOICES, default=WEBSITE_RESPONSE_VALID
    )
    response_status_code = models.IntegerField(default=0)
    response_headers = models.TextField(default="", blank=True)
    response_content = models.TextField(default="", blank=True)
    critical = models.IntegerField(default=0)
    serious = models.IntegerField(default=0)
    message = models.TextField(default="", blank=True)
    violations = models.TextField(default="", blank=True)
    results = models.TextField(default="", blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(f"#{self.id}: {self.url}")  # type: ignore
