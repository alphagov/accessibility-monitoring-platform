"""
Models - checks (called tests by the users)
"""
from typing import List, Tuple

from django.db import models
from django.urls import reverse

from ..cases.models import Case
from ..common.models import VersionModel

SCREEN_SIZE_DEFAULT = "15in"
SCREEN_SIZE_CHOICES: List[Tuple[str, str]] = [
    (SCREEN_SIZE_DEFAULT, "15 inch"),
    ("13in", "13 inch"),
]
EXEMPTION_DEFAULT = "unknown"
EXEMPTION_CHOICES: List[Tuple[str, str]] = [
    ("yes", "Yes"),
    ("no", "No"),
    (EXEMPTION_DEFAULT, "Unknown"),
]
TYPE_DEFAULT = "initial"
TYPE_CHOICES: List[Tuple[str, str]] = [
    (TYPE_DEFAULT, "Initial"),
    ("eq-retest", "Equality body retest"),
]


class Check(VersionModel):
    """
    Model for test/check
    """

    # metadata page
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="check_case",
    )
    date_of_test = models.DateTimeField(null=True, blank=True)
    description = models.TextField(default="", blank=True)
    screen_size = models.CharField(
        max_length=20,
        choices=SCREEN_SIZE_CHOICES,
        default=SCREEN_SIZE_DEFAULT,
    )
    is_exemption = models.CharField(
        max_length=20, choices=EXEMPTION_CHOICES, default=EXEMPTION_DEFAULT
    )
    notes = models.TextField(default="", blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_DEFAULT)
    check_metadata_complete_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return str(f"{self.description} | #{self.id}")  # type: ignore

    def get_absolute_url(self):
        return reverse("checks:check-metadata", kwargs={"pk": self.pk})
