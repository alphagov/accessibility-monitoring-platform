"""Models for notifications app"""
from typing import List
from django.db import models
from django.contrib.auth.models import User


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
