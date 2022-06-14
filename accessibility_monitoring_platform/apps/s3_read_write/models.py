"""Models for s3 read write app"""
from django.db import models
from django.contrib.auth.models import User
from ..cases.models import Case
from ..common.utils import amp_format_datetime

REPORT_VIEWER_URL_PATH: str = "/reports/"


class S3Report(models.Model):
    """
    Model for Case
    """

    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="report_created_by_user",
        blank=True,
        null=True,
    )
    s3_directory = models.TextField(default="", blank=True)
    version = models.IntegerField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True)
    deprecated = models.BooleanField(default=False)
    guid = models.CharField(max_length=40, blank=True)
    html = models.TextField(default="", blank=True)

    def __str__(self) -> str:
        return f"v{self.version} - {amp_format_datetime(self.created)}"

    def get_absolute_url(self):
        return f"{REPORT_VIEWER_URL_PATH}{self.guid}"
