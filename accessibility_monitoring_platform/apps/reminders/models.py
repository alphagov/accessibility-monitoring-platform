"""
Models - reminders
"""
from datetime import date
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from ..cases.models import Case


class Reminder(models.Model):
    """
    Model for reminder
    """

    case = models.ForeignKey(
        Case, on_delete=models.PROTECT, related_name="reminder_case"
    )
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="reminder_user"
    )
    due_date = models.DateField()
    description = models.TextField()
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return str(f"#{self.id} | {self.description}")  # type: ignore

    def get_absolute_url(self):
        return reverse("cases:case-detail", kwargs={"pk": self.case.id})  # type: ignore

    @property
    def tense(self):
        today: date = date.today()
        if self.due_date and self.due_date < today:
            return "past"
        if self.due_date == today:
            return "present"
        return "future"
