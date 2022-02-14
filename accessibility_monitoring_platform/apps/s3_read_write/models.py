from django.db import models
from typing import Union, Any
from django.contrib.auth.models import User
from ..cases.models import Case
import uuid
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
    guid = models.CharField(primary_key=True, max_length=40, blank=True)
    platform_version = models.IntegerField(blank=True, default=0.1)

    def save(self, *args, **kwargs):
        if not self.guid:
            self.guid = str(uuid.uuid4())

        platform_version: Union[str, None] = os.getenv("PLATFORM_VERSION")
        if platform_version and self.is_float(platform_version):
            self.platform_version = float(platform_version)
        else:
            self.platform_version = 0.1
        super().save(*args, **kwargs)

    def is_float(self, element: Any) -> bool:
        try:
            float(element)
            return True
        except ValueError:
            return False
