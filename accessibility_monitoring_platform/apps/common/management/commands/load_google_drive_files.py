import io
import mimetypes
import os
import re
from datetime import date, datetime
from unittest.mock import Mock, patch

import boto3
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from ....cases.models import BaseCase, CaseFile, User
from ....cases.views import CaseFileUploadMixin

CREATION_DATE_RE = re.compile(rb"/CreationDate\s*\(D:([^\)]*)\)")


def extract_creation_date_only(pdf_file: io.BytesIO) -> date | None:
    try:
        pdf_file.seek(0)
        data = pdf_file.getvalue()

        match = CREATION_DATE_RE.search(data)
        if not match:
            return None

        raw = match.group(1).decode("ascii", errors="ignore")

        # Grab just YYYYMMDD from the front
        m = re.match(r"(\d{4})(\d{2})(\d{2})", raw)
        if not m:
            return None

        year, month, day = map(int, m.groups())
        return date(year, month, day)
    except:
        return None


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

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        s3_prod = boto3.client("s3")

        response = s3_prod.list_objects_v2(
            Bucket=os.getenv("DB_NAME"), Prefix="google-drive-case-files/"
        )

        s3_objects = []
        while True:
            for base_obj in response.get("Contents", []):
                s3_objects.append(base_obj)

            if response.get("IsTruncated"):
                response = s3_prod.list_objects_v2(
                    Bucket=os.getenv("DB_NAME"),
                    Prefix="google-drive-case-files/",
                    ContinuationToken=response["NextContinuationToken"],
                )
            else:
                break

        s3_objects = [x for x in s3_objects if ".DS_Store" not in x["Key"]]
        num_of_s3_objects = len(s3_objects)

        s3_objects_hash = {}

        for obj in s3_objects:
            base_id = obj["Key"].split("/")[1].replace("base_case_id_", "")
            if base_id not in s3_objects_hash:
                s3_objects_hash[base_id] = []
            s3_objects_hash[base_id].append(obj["Key"])

        cases = BaseCase.objects.all()
        num_of_s3_objects_completed = 0
        for case in cases:
            if str(case.pk) not in s3_objects_hash:
                continue

            for s3_path in s3_objects_hash[str(case.pk)]:
                filename = s3_path.split("/")[-1]
                if case.casefile_set.filter(name=filename).exists() is False:
                    in_mem_file_upload = s3_to_inmemory_uploaded_file(
                        s3_prod,
                        bucket=os.getenv("DB_NAME"),
                        key=s3_path,
                    )
                    user = case.auditor if case.auditor else User.objects.get(pk=13)
                    file_type = CaseFile.Type.UNKNOWN
                    if "statement" in filename.lower():
                        file_type = CaseFile.Type.STATEMENT
                    elif "report" in filename.lower():
                        file_type = CaseFile.Type.REPORT

                    creation_date = None
                    dt = datetime.now()
                    if ".pdf" in filename:
                        creation_date = extract_creation_date_only(
                            in_mem_file_upload.file
                        )
                        if creation_date:
                            dt = datetime.combine(creation_date, datetime.min.time())
                    dt = timezone.make_aware(dt)

                    with patch(
                        "django.utils.timezone.now",
                        Mock(return_value=dt),
                    ):
                        CaseFileUploadMixin.case_file_upload(
                            self=None,
                            uploaded_file=in_mem_file_upload,
                            user=user,
                            base_case=case,
                            file_type=file_type,
                        )

                num_of_s3_objects_completed += 1
                if num_of_s3_objects_completed % 100 == 0:
                    print(
                        f">>> {num_of_s3_objects_completed} of {num_of_s3_objects} completed"
                    )
