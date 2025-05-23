"""
Models - mobile cases
"""

import json
from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from ..cases.models import UPDATE_SEPARATOR
from ..common.models import Boolean, Sector, SubCategory, VersionModel
from ..common.utils import extract_domain_from_url


class MobileCase(VersionModel):
    """
    Model for MobileCase
    """

    class AppOS(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"

    class PsbLocation(models.TextChoices):
        ENGLAND = "england", "England"
        SCOTLAND = "scotland", "Scotland"
        WALES = "wales", "Wales"
        NI = "northern_ireland", "Northern Ireland"
        UK = "uk_wide", "UK-wide"
        UNKNOWN = "unknown", "Unknown"

    class EnforcementBody(models.TextChoices):
        EHRC = "ehrc", "Equality and Human Rights Commission"
        ECNI = "ecni", "Equality Commission Northern Ireland"

    class Status(models.TextChoices):
        INITIAL = "010_initial", "Initial"
        CONTACTING = "020_contacting", "Seeking to contact"
        AUDITING = "030_auditing", "Testing"
        REPORTING = "040_reporting", "Writing report"
        QA_REPORT = "050_qa_report", "QA in progress"
        AWAIT_RESPONSE = "060_await_response", "Awaiting response"
        REVIEWING_UPDATE = "070_reviewing_update", "Reviewing update"
        REQUIRES_DECISION = "080_requires_decision", "Requires decision"
        WAITING_12_WEEKS = "090_waiting_12_weeks", "Waiting for 12-weeks"

    case_number = models.IntegerField(default=1)
    created = models.DateTimeField(blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="mobile_case_created_by",
        blank=True,
        null=True,
    )
    updated = models.DateTimeField(null=True, blank=True)

    # Case metadata page
    auditor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="mobile_case_auditor",
        blank=True,
        null=True,
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="mobile_case_reviewer",
        blank=True,
        null=True,
    )
    organisation_name = models.TextField(default="", blank=True)
    parental_organisation_name = models.TextField(default="", blank=True)
    app_name = models.TextField(default="", blank=True)
    app_store_url = models.TextField(default="", blank=True)
    domain = models.TextField(default="", blank=True)
    app_os = models.CharField(
        max_length=20,
        choices=AppOS.choices,
        default=AppOS.IOS,
    )
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, null=True, blank=True)
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    enforcement_body = models.CharField(
        max_length=20,
        choices=EnforcementBody.choices,
        default=EnforcementBody.EHRC,
    )
    psb_location = models.CharField(
        max_length=20,
        choices=PsbLocation.choices,
        default=PsbLocation.UNKNOWN,
    )
    is_complaint = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    notes = models.TextField(default="", blank=True)
    previous_case_url = models.TextField(default="", blank=True)
    trello_url = models.TextField(default="", blank=True)
    website_name = models.TextField(default="", blank=True)
    is_feedback_requested = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    case_metadata_complete_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.INITIAL,
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.organisation_name} | {self.case_identifier}"

    def get_absolute_url(self) -> str:
        return reverse("mobile:case-detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs) -> None:
        now: datetime = timezone.now()
        if not self.created:
            self.created = now
            self.domain = extract_domain_from_url(self.app_store_url)
            max_case_number = MobileCase.objects.aggregate(
                models.Max("case_number")
            ).get("case_number__max")
            if max_case_number is not None:
                self.case_number = max_case_number + 1
        self.updated = now
        super().save(*args, **kwargs)

    @property
    def title(self) -> str:
        title = f"{self.app_name} &nbsp;|&nbsp; {self.case_identifier}"
        return mark_safe(title)

    @property
    def case_identifier(self) -> str:
        return f"#M-{self.case_number}"


class EventHistory(models.Model):
    """Model to record events on platform"""

    class Type(models.TextChoices):
        UPDATE = "model_update", "Model update"
        CREATE = "model_create", "Model create"

    mobile_case = models.ForeignKey(
        MobileCase, on_delete=models.PROTECT, null=True, blank=True
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        related_name="mobile_case_event_content_type",
    )
    object_id = models.PositiveIntegerField()
    parent = GenericForeignKey("content_type", "object_id")
    event_type = models.CharField(
        max_length=100, choices=Type.choices, default=Type.UPDATE
    )
    difference = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="mobile_case_event_created_by_user",
    )
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.case} {self.content_type} {self.object_id} {self.event_type} (#{self.id})"

    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "Event histories"

    @property
    def variables(self):
        differences: dict[str, int | str] = json.loads(self.difference)

        variable_list: list[dict[str, int | str]] = []
        for key, value in differences.items():
            if self.event_type == EventHistory.Type.CREATE:
                old_value: str = ""
                new_value: int | str = value
            else:
                old_value, new_value = value.split(UPDATE_SEPARATOR, maxsplit=1)
            variable_list.append(
                {
                    "name": key,
                    "old_value": old_value,
                    "new_value": new_value,
                }
            )
        return variable_list
