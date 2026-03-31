"""
Tests for cases views
"""

import io

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse
from django.urls import reverse
from moto import mock_aws

from ...simplified.models import SimplifiedCase
from ..models import CaseFile
from ..utils import S3ReadWriteFile

CASE_FILE_NAME: str = "case_file.txt"
CASE_FILE_CONTENT: str = "Case file content"


@mock_aws
def test_case_file_create(admin_client):
    """Test that case file create uploads to S3"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    in_memory_file: InMemoryUploadedFile = InMemoryUploadedFile(
        io.BytesIO(CASE_FILE_CONTENT.encode()),
        field_name="name",
        name=CASE_FILE_NAME,
        content_type="text",
        size=len(CASE_FILE_CONTENT),
        charset=None,
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:case-file-create", kwargs={"pk": simplified_case.id}),
        {
            "file_to_upload": in_memory_file,
            "type": CaseFile.Type.STATEMENT,
            "save": "Save",
        },
    )

    assert response.status_code == 302

    case_file: CaseFile = CaseFile.objects.get(base_case=simplified_case)

    s3_read_write: S3ReadWriteFile = S3ReadWriteFile()
    data_s3: bytes | str = s3_read_write.read_case_file_from_s3(case_file=case_file)

    assert isinstance(data_s3, bytes)
    assert data_s3.decode() == CASE_FILE_CONTENT


@mock_aws
def test_document_download(admin_client):
    """Test that cases document download gets data from S3"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    case_file: CaseFile = CaseFile.objects.create(
        base_case=simplified_case,
        uploaded_by=user,
        name=CASE_FILE_NAME,
    )

    s3_read_write: S3ReadWriteFile = S3ReadWriteFile()
    s3_read_write.write_case_file_to_s3(
        case_file=case_file,
        file_content=io.BytesIO(CASE_FILE_CONTENT.encode()),
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:case-file-download", kwargs={"pk": case_file.id}),
    )

    assert response.status_code == 200

    assert response.getvalue().decode() == CASE_FILE_CONTENT
