"""
Models - reports
"""

from datetime import datetime
from typing import Dict, List, Optional

from django.contrib.auth.models import User
from django.db import models
from django.template import Context, Template
from django.urls import reverse
from django.utils import timezone

from ..cases.models import Case
from ..common.models import VersionModel
from ..common.utils import amp_format_datetime
from ..s3_read_write.models import S3Report

REPORT_VERSION_DEFAULT: str = "v1_4_0__20241005"
WRAPPER_TEXT_FIELDS: List[str] = [
    "title",
    "sent_by",
    "contact",
    "related_content",
]


class ReportWrapper(models.Model):
    """

    Model for report wrapper text.

    This contains text which wraps the report on its HTML page, is not expected
    to change but which ought not require software development to amend.
    """

    title = models.TextField(default="", blank=True)
    sent_by = models.TextField(default="", blank=True)
    contact = models.TextField(default="", blank=True)
    related_content = models.TextField(default="", blank=True)

    class Meta:
        verbose_name_plural = "Report wrapper text"
        ordering = ["-id"]

    def __str__(self) -> str:
        return str("Report wrapper text")

    def get_absolute_url(self) -> str:
        return reverse("reports:edit-report-wrapper")


class Report(VersionModel):
    """
    Model for report
    """

    case = models.OneToOneField(
        Case, on_delete=models.PROTECT, related_name="report_case"
    )
    created = models.DateTimeField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    updated = models.DateTimeField(blank=True, null=True)
    report_version = models.TextField(default=REPORT_VERSION_DEFAULT)
    report_rebuilt = models.DateTimeField(blank=True, null=True)

    # Metadata
    notes = models.TextField(default="", blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return str(f"{self.case} | {amp_format_datetime(self.created)}")

    def save(self, *args, **kwargs) -> None:
        now: datetime = timezone.now()
        if not self.created:
            self.created = now
        self.updated = now
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("reports:report-preview", kwargs={"pk": self.pk})

    @property
    def template_path(self) -> str:
        return f"reports_common/accessibility_report_{self.report_version}.html"

    @property
    def wrapper(self) -> Dict[str, str]:
        """
        Renders the template values in ReportWrapper to return the text used to
        wrap the report on its HTML page

        Returns:
            wrapper_text: Dictionary of wrapper text names and values
        """
        report_wrapper: Optional[ReportWrapper] = ReportWrapper.objects.all().first()
        wrapper_text: Dict[str, str] = {}
        if report_wrapper is not None:
            context: Context = Context({"report": self})
            for field in WRAPPER_TEXT_FIELDS:
                template: Template = Template(getattr(report_wrapper, field))
                wrapper_text[field] = template.render(context=context)
        return wrapper_text

    @property
    def latest_s3_report(self) -> Optional[S3Report]:
        """The most recently published report"""
        return self.case.s3report_set.filter(latest_published=True).last()

    @property
    def visits_metrics(self) -> Dict[str, int]:
        return {
            "number_of_visits": self.case.reportvisitsmetrics_set.all().count(),
            "number_of_unique_visitors": self.case.reportvisitsmetrics_set.values_list(
                "fingerprint_hash"
            )
            .distinct()
            .count(),
        }


class ReportVisitsMetrics(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    case = models.ForeignKey(
        Case,
        on_delete=models.SET_NULL,
        null=True,
    )
    guid = models.TextField(default="", blank=True)
    fingerprint_hash = models.IntegerField(default=0, blank=True)
    fingerprint_codename = models.TextField(default="", blank=True)

    def get_absolute_url(self) -> str:
        return reverse(
            "reports:report-metrics-view", kwargs={"pk": self.case.report.id}  # type: ignore
        )
