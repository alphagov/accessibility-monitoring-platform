"""
Models - reports
"""
from typing import Dict, List, Optional, Tuple

from django.contrib.auth.models import User
from django.db import models
from django.template import Context, Template
from django.urls import reverse
from django.utils import timezone

from ..cases.models import Case
from ..common.models import VersionModel
from ..s3_read_write.models import S3Report
from ..common.utils import amp_format_datetime

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
REPORT_VERSION_DEFAULT: str = "v1_0_0__20220406"
REPORT_VERSION_CHOICES: List[Tuple[str, str]] = [
    (REPORT_VERSION_DEFAULT, "Version 1"),
]
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
    report_version = models.TextField(default=REPORT_VERSION_DEFAULT)

    # Metadata
    notes = models.TextField(default="", blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return str(f"{self.case} | {amp_format_datetime(self.created)}")  # type: ignore

    def save(self, *args, **kwargs) -> None:
        now = timezone.now()
        if not self.created:
            self.created = now
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("reports:report-detail", kwargs={"pk": self.pk})

    @property
    def template_path(self) -> str:
        return f"reports/accessibility_report_{self.report_version}.html"

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
        return self.case.s3report_set.all().last()  # type: ignore


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
