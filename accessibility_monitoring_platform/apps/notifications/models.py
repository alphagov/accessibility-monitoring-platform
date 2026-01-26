"""Models for notifications app"""

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from ..cases.models import BaseCase, TestType
from ..common.models import Link
from ..common.templatetags.common_tags import amp_date


class CaseTask(models.Model):
    """Django model for case-specific tasks"""

    class Type(models.TextChoices):
        QA_COMMENT = "qa-comment", "QA comment"
        REPORT_APPROVED = "report-approved", "Report approved"
        REMINDER = "reminder"
        POSTCASE = "postcase", "Post case"

    type = models.CharField(max_length=20, choices=Type, default=Type.REMINDER)
    recipients = models.ManyToManyField(User)
    due_date = models.DateField()
    text = models.TextField(default="")
    base_case = models.ForeignKey(
        BaseCase,
        on_delete=models.PROTECT,
    )
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="casetask_createdby"
    )
    is_complete = models.BooleanField(default=False)
    completed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="casetask_completedby",
        blank=True,
        null=True,
    )
    updated = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_type_display()} {amp_date(self.due_date)}"

    class Meta:
        ordering: list[str] = ["-id"]


class Task(models.Model):
    """Django model for user-specific tasks"""

    class Type(models.TextChoices):
        QA_COMMENT = "qa-comment", "QA comment"
        REPORT_APPROVED = "report-approved", "Report approved"
        REMINDER = "reminder"
        OVERDUE = "overdue"
        POSTCASE = "postcase", "Post case"

    type = models.CharField(max_length=20, choices=Type, default=Type.REMINDER)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    date = models.DateField()
    base_case = models.ForeignKey(
        BaseCase,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    description = models.TextField(default="")
    read = models.BooleanField(default=False)
    action = models.TextField(default="N/A")
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_type_display()} {amp_date(self.date)}"

    class Meta:
        ordering: list[str] = ["-id"]

    def options(self) -> list[Link]:
        options: list[Link] = []
        if self.type == Task.Type.QA_COMMENT:
            url_name: str = (
                "simplified:edit-qa-comments"
                if self.base_case.test_type == TestType.SIMPLIFIED
                else "detailed:edit-qa-comments"
            )
            options.append(
                Link(
                    label="Go to QA comment",
                    url=reverse(
                        url_name,
                        kwargs={"pk": self.base_case.id},
                    ),
                ),
            )
        elif self.type == Task.Type.REPORT_APPROVED:
            url_name: str = (
                "simplified:edit-qa-approval"
                if self.base_case.test_type == TestType.SIMPLIFIED
                else "detailed:edit-qa-approval"
            )
            options.append(
                Link(
                    label="Go to Report approved",
                    url=reverse(
                        url_name,
                        kwargs={"pk": self.base_case.id},
                    ),
                ),
            )
        elif self.type == Task.Type.REMINDER:
            if self.read is True:
                options.append(
                    Link(
                        label="Create new",
                        url=reverse(
                            "notifications:reminder-create",
                            kwargs={"case_id": self.base_case.id},
                        ),
                    )
                )
            else:
                options.append(
                    Link(
                        label="Edit",
                        url=reverse(
                            "notifications:edit-reminder-task",
                            kwargs={"pk": self.id},
                        ),
                    )
                )
                options.append(
                    Link(
                        label="Delete reminder",
                        url=reverse(
                            "notifications:mark-task-read",
                            kwargs={"pk": self.id},
                        ),
                    ),
                )
        if self.type in [Task.Type.QA_COMMENT, Task.Type.REPORT_APPROVED]:
            options.append(
                Link(
                    label="Mark as seen",
                    url=reverse(
                        "notifications:mark-task-read",
                        kwargs={"pk": self.id},
                    ),
                )
            )
            options.append(
                Link(
                    label="Mark case tasks as seen",
                    url=reverse(
                        "notifications:mark-case-comments-read",
                        kwargs={"case_id": self.base_case.id},
                    ),
                ),
            )
        return options


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
