"""
Models - mobile cases
"""

import json

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.safestring import mark_safe

from ..cases.models import UPDATE_SEPARATOR, BaseCase, MobileCaseStatus
from ..common.utils import extract_domain_from_url


class MobileCase(BaseCase):
    """
    Model for MobileCase
    """

    class AppOS(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"

    Status = MobileCaseStatus

    # Case metadata page
    app_name = models.TextField(default="", blank=True)
    app_store_url = models.TextField(default="", blank=True)
    app_os = models.CharField(
        max_length=20,
        choices=AppOS.choices,
        default=AppOS.IOS,
    )
    notes = models.TextField(default="", blank=True)
    case_metadata_complete_date = models.DateField(null=True, blank=True)

    # status = models.CharField(
    #     max_length=30,
    #     choices=Status.choices,
    #     default=Status.INITIAL,
    # )

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.app_name} | {self.case_identifier}"

    def save(self, *args, **kwargs) -> None:
        if not self.domain:
            self.domain = extract_domain_from_url(self.app_store_url)
        if self.test_type != BaseCase.TestType.MOBILE:
            self.test_type = BaseCase.TestType.MOBILE
        super().save(*args, **kwargs)

    @property
    def title(self) -> str:
        title = f"{self.app_name} &nbsp;|&nbsp; {self.case_identifier}"
        return mark_safe(title)


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
        return f"{self.mobile_case} {self.content_type} {self.object_id} {self.event_type} (#{self.id})"

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


class MobileCaseHistory(models.Model):
    """Model to record history of changes to MobileCase"""

    class EventType(models.TextChoices):
        NOTE = "note", "Entered note"
        REMINDER = "reminder", "Reminder set"
        STATUS = "status", "Changed status"
        CONTACT_NOTE = "contact_note", "Entered contact note"
        RECOMMENDATION = "recommendation", "Entered enforcement recommendation"
        UNRESPONSIVE_NOTE = "unresponsive_note", "Entered unresponsive PSB note"

    mobile_case = models.ForeignKey(MobileCase, on_delete=models.PROTECT)
    event_type = models.CharField(
        max_length=20, choices=EventType.choices, default=EventType.NOTE
    )
    value = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.mobile_case} {self.event_type} {self.created} {self.created_by}"

    class Meta:
        ordering = ["-id"]
        verbose_name_plural = "Mobile Case history"
