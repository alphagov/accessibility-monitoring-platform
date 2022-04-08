from django.db import models
from typing import Union
from django.contrib.auth.models import User
from ..cases.models import Case
import os


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
    platform_version = models.CharField(blank=True, default="0.1.0", max_length=40)

    def save(self, *args, **kwargs):

        platform_version: Union[str, None] = os.getenv("PLATFORM_VERSION")
        if platform_version:
            self.platform_version = platform_version
        else:
            self.platform_version = "0.1.0"
        super().save(*args, **kwargs)
