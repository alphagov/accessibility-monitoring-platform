"""
Models - reports
"""
from typing import List, Tuple

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone

from ..cases.models import Case
from ..common.models import (
    VersionModel,
)
from ..common.utils import format_date

READY_FOR_QA_DEFAULT = "not-started"
READY_FOR_QA_CHOICES: List[Tuple[str, str]] = [
    ("yes", "Yes"),
    ("no", "No"),
    (READY_FOR_QA_DEFAULT, "Not started"),
]


class Report(VersionModel):
    """
    Model for report
    """

    case = models.ForeignKey(Case, on_delete=models.PROTECT, related_name="report_case")
    created = models.DateTimeField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="report_user",
        blank=True,
        null=True,
    )
    is_deleted = models.BooleanField(default=False)

    # Metadata
    ready_for_qa = models.CharField(
        max_length=20, choices=READY_FOR_QA_CHOICES, default=READY_FOR_QA_DEFAULT
    )
    notes = models.TextField(default="", blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return str(f"{self.case}" f" | {format_date(self.created)}")  # type: ignore

    def save(self, *args, **kwargs) -> None:
        now = timezone.now()
        if not self.created:
            self.created = now
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("reports:edit-report-metadata", kwargs={"pk": self.pk})


class BaseTemplate(VersionModel):
    """
    Model for base template (for new reports)
    """

    created = models.DateTimeField(auto_now_add=True)
    name = models.TextField()
    content = models.TextField(default="", blank=True)
    position = models.IntegerField()

    class Meta:
        ordering = ["position", "-id"]

    def __str__(self) -> str:
        return str(f"{self.name}" f" (position {self.position})")


class Section(VersionModel):
    """
    Model for section of report
    """

    report = models.ForeignKey(
        Report, on_delete=models.PROTECT, related_name="section_report"
    )
    created = models.DateTimeField(auto_now_add=True)
    name = models.TextField()
    content = models.TextField(default="", blank=True)
    position = models.IntegerField()

    def __str__(self) -> str:
        return str(f"{self.report} - {self.name}" f" (position {self.position})")
