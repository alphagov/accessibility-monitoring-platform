"""
Tests for cases views
"""

import io

from moto import mock_aws

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse
from django.urls import reverse

from ...simplified.models import SimplifiedCase
from ..models import DocumentUpload
from ..utils import S3ReadWriteDocument

UPLOAD_FILE_NAME: str = "upload_file.txt"
UPLOAD_FILE_CONTENT: str = "Upload file content"


@mock_aws
def test_document_upload(admin_client):
    """Test that cases document upload saves to S3"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    in_memory_file: InMemoryUploadedFile = InMemoryUploadedFile(
        io.BytesIO(UPLOAD_FILE_CONTENT.encode()),
        field_name="name",
        name=UPLOAD_FILE_NAME,
        content_type="text",
        size=len(UPLOAD_FILE_CONTENT),
        charset=None,
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:document-upload-create", kwargs={"pk": simplified_case.id}),
        {
            "file_to_upload": in_memory_file,
            "type": DocumentUpload.Type.STATEMENT,
            "save": "Save",
        },
    )

    assert response.status_code == 302

    document_upload: DocumentUpload = DocumentUpload.objects.get(
        base_case=simplified_case
    )

    s3_read_write: S3ReadWriteDocument = S3ReadWriteDocument()
    data_s3: bytes | str = s3_read_write.get_document_from_s3(
        document_upload=document_upload
    )

    assert isinstance(data_s3, bytes)
    assert data_s3.decode() == UPLOAD_FILE_CONTENT


@mock_aws
def test_document_download(admin_client):
    """Test that cases document download gets data from S3"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    document_upload: DocumentUpload = DocumentUpload.objects.create(
        base_case=simplified_case,
        uploaded_by=user,
        name=UPLOAD_FILE_NAME,
    )

    s3_read_write: S3ReadWriteDocument = S3ReadWriteDocument()
    s3_read_write.put_document_to_s3(
        document_upload=document_upload,
        file_content=io.BytesIO(UPLOAD_FILE_CONTENT.encode()),
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:document-upload-download", kwargs={"pk": document_upload.id}),
    )

    assert response.status_code == 200

    assert response.getvalue().decode() == UPLOAD_FILE_CONTENT
