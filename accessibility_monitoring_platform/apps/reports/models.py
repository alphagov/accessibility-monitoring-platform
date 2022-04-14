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

TEMPLATE_TYPE_DEFAULT = "markdown"
TEMPLATE_TYPE_HTML = "html"
TEMPLATE_TYPE_URLS = "urls"
TEMPLATE_TYPE_ISSUES = "issues"
TEMPLATE_TYPE_CHOICES: List[Tuple[str, str]] = [
    (TEMPLATE_TYPE_DEFAULT, "Markdown"),
    (TEMPLATE_TYPE_URLS, "Contains URL table"),
    (TEMPLATE_TYPE_ISSUES, "Contains Issues table"),
    (TEMPLATE_TYPE_HTML, "HTML"),
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
        blank=True,
        null=True,
    )
    is_deleted = models.BooleanField(default=False)

    # Metadata
    notes = models.TextField(default="", blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return str(f"{self.case} | {format_date(self.created)}")  # type: ignore

    def save(self, *args, **kwargs) -> None:
        now = timezone.now()
        if not self.created:
            self.created = now
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("reports:report-detail", kwargs={"pk": self.pk})


class BaseTemplate(VersionModel):
    """
    Model for base template (for new reports)
    """

    created = models.DateTimeField(auto_now_add=True)
    name = models.TextField()
    template_type = models.CharField(
        max_length=20, choices=TEMPLATE_TYPE_CHOICES, default=TEMPLATE_TYPE_DEFAULT
    )
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
        Report,
        on_delete=models.PROTECT,
    )
    created = models.DateTimeField(auto_now_add=True)
    name = models.TextField()
    template_type = models.CharField(
        max_length=20, choices=TEMPLATE_TYPE_CHOICES, default=TEMPLATE_TYPE_DEFAULT
    )
    content = models.TextField(default="", blank=True)
    position = models.IntegerField()

    class Meta:
        ordering = ["report", "position"]

    def __str__(self) -> str:
        return str(f"{self.report} - {self.name} (position {self.position})")

    @property
    def anchor(self) -> str:
        return f"report-section-{self.id}"  # type: ignore

    @property
    def has_table(self):
        return self.tablerow_set.count() > 0  # type: ignore

    @property
    def visible_table_rows(self):
        return self.tablerow_set.filter(is_deleted=False)  # type: ignore


class TableRow(VersionModel):
    """
    Model for row of table in report
    """

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    cell_content_1 = models.TextField(default="", blank=True)
    cell_content_2 = models.TextField(default="", blank=True)
    row_number = models.IntegerField()

    class Meta:
        ordering = ["section", "row_number"]

    def __str__(self) -> str:
        return str(f"{self.section}: Table row {self.row_number}")


class PublishedReport(models.Model):
    """
    Model for published report
    """

    report = models.ForeignKey(
        Report,
        on_delete=models.PROTECT,
    )
    version = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    html_content = models.TextField(default="", blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return str(f"v{self.version} - {self.created.strftime('%H:%M')} {format_date(self.created)}")  # type: ignore

    def save(self, *args, **kwargs) -> None:
        now = timezone.now()
        if not self.created:
            self.created = now
            self.version = self.report.publishedreport_set.count() + 1  # type: ignore
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("reports:report-publish", kwargs={"pk": self.pk})
