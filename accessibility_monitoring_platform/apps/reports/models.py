"""
Models - reports
"""
from django.db import models
from django.urls import reverse
from django.utils import timezone

from ..cases.models import Case
from ..common.models import (
    VersionModel,
)
from ..common.utils import format_date


class Report(VersionModel):
    """
    Model for report
    """

    case = models.ForeignKey(Case, on_delete=models.PROTECT, related_name="report_case")
    created = models.DateTimeField()
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return str(
            f"{self.case}" f" | {format_date(self.created)}"  # type: ignore
        )

    def save(self, *args, **kwargs) -> None:
        now = timezone.now()
        if not self.created:
            self.created = now
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("reports:edit-report-metadata", kwargs={"pk": self.pk})
