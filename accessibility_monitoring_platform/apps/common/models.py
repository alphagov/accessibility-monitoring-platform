"""
Models for common data used across project
"""
from typing import Dict, List, Tuple

import json

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

BOOLEAN_DEFAULT: str = "no"
BOOLEAN_FALSE: str = BOOLEAN_DEFAULT
BOOLEAN_TRUE: str = "yes"
BOOLEAN_CHOICES: List[Tuple[str, str]] = [
    (BOOLEAN_TRUE, "Yes"),
    (BOOLEAN_FALSE, "No"),
]

EVENT_TYPE_DEFAULT: str = "model_update"
EVENT_TYPE_MODEL_UPDATE: str = EVENT_TYPE_DEFAULT
EVENT_TYPE_MODEL_CREATE: str = "model_create"
EVENT_TYPES: Dict[str, str] = {
    EVENT_TYPE_DEFAULT: "Model update",
    EVENT_TYPE_MODEL_CREATE: "Model create",
}
EVENT_TYPE_CHOICES: List[Tuple[str, str]] = [
    (key, value) for key, value in EVENT_TYPES.items()
]
ACCESSIBILITY_STATEMENT_DEFAULT: str = """# Accessibility statement

Placeholder for platform."""
PRIVACY_NOTICE_DEFAULT: str = """# Privacy notice

Placeholder for platform."""
MORE_INFORMATION_ABOUT_MONITORING_DEFAULT: str = """# More Information

More information about monitoring placeholder"""


class Sector(models.Model):
    """
    Model for website/organisation sector
    """

    name = models.CharField(max_length=200)

    def __str__(self):
        return str(self.name)


class IssueReport(models.Model):
    """
    Model for reported issue about a page on the site
    """

    page_url = models.CharField(max_length=200)
    page_title = models.CharField(max_length=200)
    description = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="issue_report_created_by_user",
    )
    created = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    trello_ticket = models.CharField(max_length=200, default="", blank=True)
    notes = models.TextField(default="", blank=True)

    def __str__(self):
        return f"#{self.id} {self.page_title}"


class Platform(models.Model):
    """
    Settings for platform as a whole
    """

    active_qa_auditor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="platform_active_qa_auditor",
        blank=True,
        null=True,
    )
    platform_accessibility_statement = models.TextField(
        default=ACCESSIBILITY_STATEMENT_DEFAULT, blank=True
    )
    platform_privacy_notice = models.TextField(
        default=PRIVACY_NOTICE_DEFAULT, blank=True
    )
    report_viewer_accessibility_statement = models.TextField(default="", blank=True)
    report_viewer_privacy_notice = models.TextField(default="", blank=True)
    markdown_cheatsheet = models.TextField(default="", blank=True)
    more_information_about_monitoring = models.TextField(
        default=MORE_INFORMATION_ABOUT_MONITORING_DEFAULT, blank=True
    )

    class Meta:
        verbose_name_plural = "Platform settings"

    def __str__(self):
        return "Platform settings"


class ChangeToPlatform(models.Model):
    """
    Record of platform changes made and deployed.
    """

    name = models.CharField(max_length=200)
    notes = models.TextField(default="", blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name_plural: str = "changes to platform"

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self) -> str:
        return reverse("common:platform-history")


class Event(models.Model):
    """
    Model to records events on platform
    """

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    parent = GenericForeignKey("content_type", "object_id")
    type = models.CharField(
        max_length=100, choices=EVENT_TYPE_CHOICES, default=EVENT_TYPE_DEFAULT
    )
    value = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="event_created_by_user",
    )
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"#{self.content_type} {self.object_id} {self.type}"

    class Meta:
        ordering = ["-created"]

    @property
    def old_fields(self):
        """Return old values of fields"""
        value_dict = json.loads(self.value)
        if "old" in value_dict:
            return json.loads(value_dict["old"])[0]["fields"]
        return ""

    @property
    def new_fields(self):
        """Return new values of fields"""
        return json.loads(json.loads(self.value).get("new", ""))[0]["fields"]

    @property
    def diff(self):
        """Return differences between old and new values of fields"""
        if self.old_fields == "":
            return self.new_fields
        diff = {}
        for key in self.new_fields:
            if key in self.old_fields:
                if self.old_fields[key] != self.new_fields[key]:
                    diff[key] = f"{self.old_fields[key]} -> {self.new_fields[key]}"
            else:
                diff[key] = f"-> {self.new_fields[key]}"
        for key in self.old_fields:
            if key not in self.new_fields:
                diff[key] = f"{self.old_fields[key]} ->"
        return diff


class VersionModel(models.Model):
    """
    Model subclass to add versioning
    """

    version = models.IntegerField(default=0)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.version += 1
        super().save(*args, **kwargs)


class UserCacheUniqueHash(models.Model):
    """
    Caches user ID. Used for excluding users from report logs.
    """

    user = models.OneToOneField(User, on_delete=models.PROTECT, primary_key=True)
    fingerprint_hash = models.IntegerField(default=0, blank=True)


class FrequentlyUsedLink(models.Model):
    """
    Model for frequently used links
    """

    label = models.TextField(default="", blank=True)
    url = models.TextField(default="", blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self) -> str:
        return str(f"{self.label}: {self.url}")
