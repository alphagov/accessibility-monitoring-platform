"""Models for comments and comment history"""
from typing import List
from django.db import models
from django.contrib.auth.models import User
from accessibility_monitoring_platform.apps.cases.models import Case


class Comments(models.Model):
    """ Comments model """

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="comment_case",
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="poster_user",
        blank=True,
        null=True,
    )
    page = models.TextField()
    body = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(null=True, blank=True)
    hidden = models.BooleanField(default=False)
    path = models.TextField(default=False)

    class Meta:
        ordering: List[str] = ["created_date"]
        verbose_name: str = "Comment"
        verbose_name_plural: str = "Comments"

    def __str__(self) -> str:
        return f"Comment {self.body} by {self.user}"


class CommentsHistory(models.Model):
    """ Comments history model """

    comment = models.ForeignKey(
        Comments,
        on_delete=models.CASCADE,
        related_name="comment",
        blank=True,
        null=True,
    )
    before = models.TextField()
    after = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name: str = "Comment history"
        verbose_name_plural: str = "Comments history"
