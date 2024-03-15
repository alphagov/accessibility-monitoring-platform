"""Models for comments and user-specific alerts"""

from typing import Dict, List

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone

from accessibility_monitoring_platform.apps.cases.models import Case


class Comment(models.Model):
    """Comment model"""

    class Type(models.TextChoices):
        QA = "qa", "QA"
        EXPORT = "export", "Equality body export"

    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.QA,
    )
    case = models.ForeignKey(
        Case,
        on_delete=models.PROTECT,
        related_name="comment_case",
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="poster_user",
        blank=True,
        null=True,
    )
    body = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    hidden = models.BooleanField(default=False)
    updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering: List[str] = ["created_date"]

    def __str__(self) -> str:
        return f"Comment {self.body} by {self.user}"

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        super().save(*args, **kwargs)


class Alert(models.Model):
    """Alert for a specific user model"""

    class Type(models.TextChoices):
        QA_COMMENT = "qa-comment", "QA comment"
        REPORT_APPROVED = "report-approved", "Report approved"
        REMINDER = "reminder", "Reminder"

    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.QA_COMMENT,
    )
    target_user = models.ForeignKey(User, on_delete=models.PROTECT)
    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    comment = models.ForeignKey(
        Comment, on_delete=models.PROTECT, blank=True, null=True
    )
    message = models.TextField(default="")
    read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    due_date = models.DateField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return str(f"{self.get_type_display()} | #{self.message}")

    def get_absolute_url(self):
        return reverse("cases:case-detail", kwargs={"pk": self.case.id})

    @property
    def target_url(self) -> str:
        case_pk_id: Dict[str, int] = {"pk": self.case.id}
        if self.type == Alert.Type.REPORT_APPROVED:
            return reverse("cases:edit-report-approved", kwargs=case_pk_id)
        return reverse("cases:edit-qa-comments", kwargs=case_pk_id)

    @property
    def target_label(self) -> str:
        label_prefix: str = f"{self.case} - "
        if self.type == Alert.Type.REPORT_APPROVED:
            label_prefix += "Report approved"
        else:
            label_prefix += "COMMENT"
        return label_prefix
