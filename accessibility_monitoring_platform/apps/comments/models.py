"""Models for comment and comment history"""
from typing import List
from django.db import models
from django.contrib.auth.models import User
from accessibility_monitoring_platform.apps.cases.models import Case


class Comment(models.Model):
    """Comment model"""

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
    updated_date = models.DateTimeField(null=True, blank=True)
    hidden = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: List[str] = ["created_date"]

    def __str__(self) -> str:
        return f"Comment {self.body} by {self.user}"
