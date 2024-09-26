"""
Models for common data used across project
"""

from dataclasses import dataclass
from datetime import date

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template import Context, Template
from django.urls import reverse

ACCESSIBILITY_STATEMENT_DEFAULT: str = """# Accessibility statement

Placeholder for platform."""
PRIVACY_NOTICE_DEFAULT: str = """# Privacy notice

Placeholder for platform."""
MORE_INFORMATION_ABOUT_MONITORING_DEFAULT: str = """# More Information

More information about monitoring placeholder"""


class Boolean(models.TextChoices):
    YES = "yes"
    NO = "no"


@dataclass
class Link:
    label: str
    url: str


class StartEndDateManager(models.Manager):
    """Model manager which filters by date"""

    def on_date(self, target_date: date):
        return (
            super()
            .get_queryset()
            .exclude(date_start__gt=target_date)
            .exclude(date_end__lt=target_date)
        )


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

    issue_number = models.IntegerField(default=1)
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

    class Meta:
        ordering = ["-issue_number"]

    def save(self, *args, **kwargs) -> None:
        if self.id is None:
            max_issue_number = IssueReport.objects.aggregate(
                models.Max("issue_number")
            ).get("issue_number__max")
            if max_issue_number is not None:
                self.issue_number = max_issue_number + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.issue_number} {self.page_title}"

    def get_absolute_url(self) -> str:
        return self.page_url


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

    class Type(models.TextChoices):
        UPDATE = "model_update", "Model update"
        CREATE = "model_create", "Model create"

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    parent = GenericForeignKey("content_type", "object_id")
    type = models.CharField(max_length=100, choices=Type.choices, default=Type.UPDATE)
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

    def get_absolute_url(self) -> str:
        return self.url


class FooterLink(models.Model):
    """
    Model for links in footer
    """

    label = models.TextField(default="", blank=True)
    url = models.TextField(default="", blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self) -> str:
        return str(f"{self.label}: {self.url}")

    def get_absolute_url(self) -> str:
        return self.url


class SubCategory(models.Model):
    """
    Model to record sub-category of case's organisation
    (such as Jobs, Local offer/SEND, Adult education)
    """

    name = models.TextField(default="", blank=True)

    class Meta:
        verbose_name_plural = "Sub categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class EmailTemplate(models.Model):
    """Email template"""

    class Type(models.TextChoices):
        SIMPLE = "simple"
        COMPLEX = "complex"

    class Slug(models.TextChoices):
        DEFAULT = "default"
        TWELVE_WEEK_REQUEST = "12-week-request", "12-week update request"
        OUTSTANDING_ISSUES = "outstanding-issues", "Outstanding issues"
        EQUALITY_BODY_RETEST = "equality-body-retest", "Equality body retest"

    name = models.TextField(default="Default")
    type = models.CharField(max_length=20, choices=Type, default=Type.SIMPLE)
    slug = models.CharField(max_length=50, choices=Slug, default=Slug.DEFAULT)
    template = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_by_user",
        null=True,
        blank=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="updated_by_user",
        null=True,
        blank=True,
    )
    updated = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def render(self, context: dict) -> str:
        """Render email template using context and return result"""
        template: Template = Template(self.template)
        return template.render(context=Context(context))
