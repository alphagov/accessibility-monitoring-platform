import io
import mimetypes
import os

import boto3
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import InMemoryUploadedFile

from ....cases.models import BaseCase, DocumentUpload, DocumentUpload
from ....cases.views import DocumentUploadMixin
from ....cases.models import User


def s3_to_inmemory_uploaded_file(s3, bucket: str, key: str) -> InMemoryUploadedFile:
    response = s3.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read()  # bytes from S3

    file_obj = io.BytesIO(content)
    file_size = len(content)

    filename = key.split("/")[-1]
    content_type = (
        response.get("ContentType")
        or mimetypes.guess_type(filename)[0]
        or "application/octet-stream"
    )

    return InMemoryUploadedFile(
        file=file_obj,
        field_name="file",
        name=filename,
        content_type=content_type,
        size=file_size,
        charset=None,
    )


class Command(BaseCommand):
    help = "Command for loading Google Drive platform files to the platform"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_limit",
            nargs="?",
            type=int,
            help="Limit number of files to load for testing purposes"
        )

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        file_limit = options["file_limit"]
        s3_prod = boto3.client("s3")

        response = s3_prod.list_objects_v2(
            Bucket=os.getenv("DB_NAME"),
            Prefix="google-drive-case-files/"
        )

        s3_objects = []
        while True:
            for base_obj in response.get("Contents", []):
                s3_objects.append(base_obj)

            if response.get("IsTruncated"):
                response = s3_prod.list_objects_v2(
                    Bucket=os.getenv("DB_NAME"),
                    Prefix="google-drive-case-files/",
                    ContinuationToken=response["NextContinuationToken"]
                )
            else:
                break

        s3_objects = [x for x in s3_objects if ".DS_Store" not in x["Key"]]
        num_of_s3_objects = len(s3_objects)

        for n, key in enumerate(s3_objects[:file_limit]):
            if n % 100 == 0:
                print(f">>> {n} of {num_of_s3_objects} completed")

            file_path = key["Key"]
            base_id = file_path.split("/")[1].replace("base_case_id_", "")
            base_obj = BaseCase.objects.get(pk=base_id)
            in_mem_file_upload = s3_to_inmemory_uploaded_file(
                s3_prod,
                bucket=os.getenv("DB_NAME"),
                key=key["Key"],
            )
            user = base_obj.auditor if base_obj.auditor else User.objects.get(pk=13)
            DocumentUploadMixin.document_upload(
                self=None,
                uploaded_file=in_mem_file_upload,
                user=user,
                base_case=base_obj,
                document_type=DocumentUpload.Type.UNKNOWN
            )
