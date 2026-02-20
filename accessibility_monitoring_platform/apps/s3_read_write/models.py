"""Models for s3 read write app"""

from pathlib import Path
import os

import boto3
from django.contrib.auth.models import User
from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage
from uuid import uuid4

from ..cases.models import BaseCase
from ..common.utils import amp_format_datetime
from ...settings.base import DATABASES, DEBUG, S3_MOCK_ENDPOINT, UNDER_TEST

REPORT_VIEWER_URL_PATH: str = "/reports/"


class S3Report(models.Model):
    """
    Model for Case
    """

    base_case = models.ForeignKey(
        BaseCase,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
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
    latest_published = models.BooleanField(default=False)
    guid = models.CharField(max_length=40, blank=True)
    html = models.TextField(default="", blank=True)

    def __str__(self) -> str:
        return f"v{self.version} - {amp_format_datetime(self.created)}"

    def get_absolute_url(self):
        return f"{REPORT_VIEWER_URL_PATH}{self.guid}"


class InvoiceFileS3Storage(S3Boto3Storage):
    location = "invoices"
    bucket_name = ""
    endpoint_url = S3_MOCK_ENDPOINT
    region_name = "us-east-1"
    addressing_style = "path"
    use_ssl = False
    verify = False

    def __init__(self, **settings):
        super().__init__(**settings)
        self.s3_client = boto3.client(
            "s3",
            region_name=DATABASES["aws-s3-bucket"]["aws_region"],
            aws_access_key_id=DATABASES["aws-s3-bucket"]["aws_access_key_id"],
            aws_secret_access_key=DATABASES["aws-s3-bucket"]["aws_secret_access_key"],
            endpoint_url=S3_MOCK_ENDPOINT,
        )

        # Creates bucket for unit testing, integration testing, and local development
        if DEBUG or UNDER_TEST:
            response = self.s3_client.list_buckets()
            bucket_names = [bucket["Name"] for bucket in response["Buckets"]]
            if DATABASES["aws-s3-bucket"]["bucket_name"] not in bucket_names:
                self.s3_client.create_bucket(
                    Bucket=DATABASES["aws-s3-bucket"]["bucket_name"],
                )

        self.bucket_name: str = DATABASES["aws-s3-bucket"]["bucket_name"]


def get_invoice_s3_file_path(instance: "Invoice", filename: str) -> str:
    ext = Path(filename).suffix  # includes the dot, e.g. ".pdf"
    return f"{uuid4().hex}{ext}"


class Invoice(models.Model):
    cost_center = models.CharField(max_length=255)
    generated_at = models.DateTimeField(auto_now_add=True)
    original_filename = models.CharField(max_length=255, blank=True)


    file = models.FileField(
        storage=InvoiceFileS3Storage(),
        upload_to=get_invoice_s3_file_path,
        max_length=255,  # 100 can be tight if you later add folders
    )

    def __str__(self) -> str:
        return f"Invoice no.{self.pk}"

    def open(self):
        # Usually you don't need this method at all, but if you keep it:
        self.file.open("rb")
        return self.file
    
    def save(self, *args, **kwargs):
        if self.file and not self.original_filename:
            # self.file.file is the underlying UploadedFile in many cases
            src_name = getattr(getattr(self.file, "file", None), "name", None) or self.file.name
            self.original_filename = os.path.basename(src_name)
        super().save(*args, **kwargs)
