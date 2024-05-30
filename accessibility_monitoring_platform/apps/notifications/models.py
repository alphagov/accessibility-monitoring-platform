"""Models for notifications app"""

from dataclasses import dataclass
from typing import Dict, List

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from ..cases.models import Case, CaseStatus


@dataclass
class Option:
    label: str
    url: str


class Task(models.Model):
    """Django model for user-specific tasks"""

    class Type(models.TextChoices):
        QA_COMMENT = "qa-comment", "QA comment"
        REPORT_APPROVED = "report-approved"
        REMINDER = "reminder"
        OVERDUE = "overdue"
        POSTCASE = "postcase", "Post case"

    type = models.CharField(max_length=20, choices=Type, default=Type.REMINDER)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    date = models.DateField()
    case = models.ForeignKey(Case, on_delete=models.PROTECT, blank=True, null=True)
    description = models.TextField(default="")
    read = models.BooleanField(default=False)
    action = models.TextField(default="N/A")

    def options(self) -> List[Option]:
        options: List[Option] = []
        if self.type == Task.Type.QA_COMMENT:
            options.append(
                Option(
                    label="Go to QA comment",
                    url=reverse(
                        "cases:edit-qa-comments",
                        kwargs={"pk": self.case.id},
                    ),
                ),
            )
        elif self.type == Task.Type.REPORT_APPROVED:
            options.append(
                Option(
                    label="Go to Report approved",
                    url=reverse(
                        "cases:edit-report-approved",
                        kwargs={"pk": self.case.id},
                    ),
                ),
            )
        elif self.type == Task.Type.REMINDER:
            options.append(
                Option(
                    label="Edit",
                    url=reverse(
                        "notifications:edit-reminder-task",
                        kwargs={"pk": self.id},
                    ),
                )
            )
            options.append(
                Option(
                    label="Delete reminder",
                    url=reverse(
                        "notifications:mark-task-read",
                        kwargs={"pk": self.id},
                    ),
                ),
            )
        if self.type == Task.Type.OVERDUE:
            kwargs_case_pk: Dict[str, int] = {"pk": self.case.id}
            if self.case.status.status == CaseStatus.Status.REPORT_READY_TO_SEND:
                option: Option = Option(
                    label="Seven day 'no contact details' response overdue",
                    url=reverse(
                        "cases:edit-find-contact-details", kwargs=kwargs_case_pk
                    ),
                )
            elif self.case.status.status == CaseStatus.Status.IN_REPORT_CORES:
                option: Option = Option(
                    label=self.case.in_report_correspondence_progress,
                    url=reverse("cases:edit-cores-overview", kwargs=kwargs_case_pk),
                )
            elif self.case.status.status == CaseStatus.Status.AWAITING_12_WEEK_DEADLINE:
                option: Option = Option(
                    label="Overdue",
                    url=reverse("cases:edit-cores-overview", kwargs=kwargs_case_pk),
                )
            elif self.case.status.status == CaseStatus.Status.IN_12_WEEK_CORES:
                option: Option = Option(
                    label=self.case.twelve_week_correspondence_progress,
                    url=reverse("cases:edit-cores-overview", kwargs=kwargs_case_pk),
                )
            options.append(option)
        if self.type in [Task.Type.QA_COMMENT, Task.Type.REPORT_APPROVED]:
            options.append(
                Option(
                    label="Mark as seen",
                    url=reverse(
                        "notifications:mark-task-read",
                        kwargs={"pk": self.id},
                    ),
                )
            )
        return options


class Notification(models.Model):
    """Django model for notifications"""

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="notification_user",
        blank=True,
        null=True,
    )
    body = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    path = models.TextField(default="")
    list_description = models.TextField(default="")

    class Meta:
        ordering: List[str] = ["-created_date"]
        verbose_name: str = "Notification"
        verbose_name_plural: str = "Notifications"

    def __str__(self) -> str:
        return f"Notification {self.body} for {self.user}"


class NotificationSetting(models.Model):
    """Django model for notifications settings"""

    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name="notification_settings_user",
        primary_key=True,
    )
    email_notifications_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name: str = "NotificationSetting"
        verbose_name_plural: str = "NotificationSettings"

    def __str__(self) -> str:
        return f"{self.user} - email_notifications_enabled is {self.email_notifications_enabled}"
