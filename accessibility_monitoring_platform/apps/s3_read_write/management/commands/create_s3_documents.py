"""Command to create and load dummy S3 documents"""

from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from ...models import Invoice, InvoiceFileS3Storage
from .....settings.base import DATABASES, DEBUG, S3_MOCK_ENDPOINT, UNDER_TEST


def make_pdf_bytes(text: str) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.drawString(50, 800, text)
    c.showPage()
    c.save()
    return buf.getvalue()


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
        InvoiceFileS3Storage()
        s3_client = boto3.client(
            "s3",
            region_name=DATABASES["aws-s3-bucket"]["aws_region"],
            aws_access_key_id=DATABASES["aws-s3-bucket"]["aws_access_key_id"],
            aws_secret_access_key=DATABASES["aws-s3-bucket"]["aws_secret_access_key"],
            endpoint_url=S3_MOCK_ENDPOINT,
        )

        if DEBUG or UNDER_TEST:
            response = s3_client.list_buckets()
            bucket_names = [bucket["Name"] for bucket in response["Buckets"]]
            if DATABASES["aws-s3-bucket"]["bucket_name"] not in bucket_names:
                s3_client.create_bucket(
                    Bucket=DATABASES["aws-s3-bucket"]["bucket_name"],
                )
        else:
            raise Exception("This command should only be triggered in local and testing environments")

        bucket_name: str = DATABASES["aws-s3-bucket"]["bucket_name"]

        query_set_length: int = Invoice.objects.all().count()
        for n, invoice in enumerate(Invoice.objects.all()):
            if n % 5 == 0:
                print(f">>> processing {n} of {query_set_length}")
            key: str = invoice.file.storage._normalize_name(invoice.file.name)
            pdf_data: bytes = make_pdf_bytes(f"Test PDF - {invoice.file.name}")
            s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=pdf_data,
                ContentType="application/pdf",
            )
        print(f">>> created {query_set_length} dummy files")
        print(">>> Run 'make check_s3_files' to ensure the files have been added correctly")
