"""
Models for common data used across project
"""
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

EVENT_TYPE_DEFAULT = "model_update"
EVENT_TYPE_MODEL_CREATE = "model_create"
EVENT_TYPES = {
    EVENT_TYPE_DEFAULT: "Model update",
    EVENT_TYPE_MODEL_CREATE: "Model create",
}
EVENT_TYPE_CHOICES = [(key, value) for key, value in EVENT_TYPES.items()]


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
        on_delete=models.CASCADE,
        related_name="issue_report_created_by_user",
    )
    created = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    trello_ticket = models.CharField(max_length=200, default="", blank=True)
    notes = models.TextField(default="", blank=True)

    def __str__(self):
        return f"#{self.id} {self.page_title}"  # type: ignore


class Event(models.Model):
    """
    Model to records events on platform
    """

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    parent = GenericForeignKey("content_type", "object_id")
    type = models.CharField(
        max_length=100, choices=EVENT_TYPE_CHOICES, default=EVENT_TYPE_DEFAULT
    )
    value = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="event_created_by_user",
    )
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"#{self.parent} {self.type}"

    class Meta:
        ordering = ["-created"]
