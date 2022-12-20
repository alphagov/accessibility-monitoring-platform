"""Models for recording results of bulk testing of websites"""
from typing import List, Tuple
from django.db import models


WEBSITE_RESPONSE_VALID: str = "200"
WEBSITE_RESPONSE_ERROR: str = "error"
WEBSITE_RESPONSE_OTHER: str = "other"
WEBSITE_RESPONSE_CHOICES: List[Tuple[str, str]] = [
    (WEBSITE_RESPONSE_VALID, "Valid"),
    (WEBSITE_RESPONSE_ERROR, "Error"),
    (WEBSITE_RESPONSE_OTHER, "Other"),
]


class Website(models.Model):
    """Websites tested for accessibility"""

    url = models.TextField(default="", blank=True)
    response_type = models.CharField(
        max_length=10, choices=WEBSITE_RESPONSE_CHOICES, default=WEBSITE_RESPONSE_VALID
    )
    response_status_code = models.IntegerField(default=0)
    response_headers = models.TextField(default="", blank=True)
    response_content = models.TextField(default="", blank=True)
    axe_core_critical_count = models.IntegerField(default=0)
    axe_core_serious_count = models.IntegerField(default=0)
    axe_core_message = models.TextField(default="", blank=True)
    axe_core_violations = models.TextField(default="", blank=True)
    axe_core_results = models.TextField(default="", blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return str(f"#{self.id}: {self.url}")  # type: ignore
