"""Command to create and load dummy S3 documents"""

import boto3
from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand

from ...models import Invoice
from .....settings.base import DATABASES, S3_MOCK_ENDPOINT


def s3_file_exists(s3, bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise  # real error (permissions, network, etc.)


class Command(BaseCommand):
    """Command to create and load dummy S3 documents"""
    def handle(self, *args, **options):  # pylint: disable=unused-argument
        s3 = boto3.client(
            "s3",
            region_name=DATABASES["aws-s3-bucket"]["aws_region"],
            aws_access_key_id=DATABASES["aws-s3-bucket"]["aws_access_key_id"],
            aws_secret_access_key=DATABASES["aws-s3-bucket"]["aws_secret_access_key"],
            endpoint_url=S3_MOCK_ENDPOINT,
        )
        bucket_name: str = DATABASES["aws-s3-bucket"]["bucket_name"]

        query_set_length: int = Invoice.objects.all().count()
        errors: int = 0
        for n, invoice in enumerate(Invoice.objects.all()):
            if n % 5 == 0:
                print(f">>> Checking {n} of {query_set_length}")
            key: str = invoice.file.storage._normalize_name(invoice.file.name)
            if not s3_file_exists(s3, bucket_name, key):
                errors += 1
                print(f">>> Could not find {invoice.file.name}")

        if errors:
            print(f">>> {errors} files missing ❌")
        else:
            print(">>> All files found in local S3 ✅")

        print(">>> Printing head of S3 file list...")
        response = s3.list_objects_v2(Bucket=bucket_name)
        for obj in response.get("Contents", [])[:5]:
            print(obj["Key"])
