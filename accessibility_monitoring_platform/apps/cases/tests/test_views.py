"""
Tests for cases views
"""

import io
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse
from django.urls import reverse

from ...simplified.models import SimplifiedCase
from ..models import DocumentUpload

UPLOAD_FILE_NAME: str = "upload_file.txt"
UPLOAD_FILE_CONTENT: str = "Upload file content"


@patch("accessibility_monitoring_platform.apps.cases.views.S3ReadWriteDocument")
def test_document_upload(mock_s3_read_write, admin_client):
    """Test that cases document upload saves to S3"""
    mock_put_document_to_s3: MagicMock = MagicMock()
    mock_s3_read_write_instance: MagicMock = MagicMock()
    mock_s3_read_write_instance.put_document_to_s3 = mock_put_document_to_s3
    mock_s3_read_write.return_value = mock_s3_read_write_instance

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    path_kwargs: dict[str, int] = {"pk": simplified_case.id}

    in_memory_file: InMemoryUploadedFile = InMemoryUploadedFile(
        io.BytesIO(UPLOAD_FILE_CONTENT.encode()),
        field_name="name",
        name=UPLOAD_FILE_NAME,
        content_type="text",
        size=len(UPLOAD_FILE_CONTENT),
        charset=None,
    )

    response: HttpResponse = admin_client.post(
        reverse("cases:document-upload-create", kwargs=path_kwargs),
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

    assert document_upload.name == UPLOAD_FILE_NAME

    assert mock_put_document_to_s3.called is True

    assert isinstance(
        mock_put_document_to_s3.call_args[1]["document_upload"], DocumentUpload
    )
    assert (
        mock_put_document_to_s3.call_args[1]["document_upload"].name == UPLOAD_FILE_NAME
    )

    assert isinstance(
        mock_put_document_to_s3.call_args[1]["file_content"], InMemoryUploadedFile
    )
    assert mock_put_document_to_s3.call_args[1]["file_content"].name == UPLOAD_FILE_NAME
    assert mock_put_document_to_s3.call_args[1]["file_content"].size == len(
        UPLOAD_FILE_CONTENT
    )


@patch("accessibility_monitoring_platform.apps.cases.views.S3ReadWriteDocument")
def test_document_download(mock_s3_read_write, admin_client):
    """Test that cases document download gets data from S3"""
    mock_get_document_from_s3: MagicMock = MagicMock()
    mock_get_document_from_s3.return_value = UPLOAD_FILE_CONTENT.encode()
    mock_s3_read_write_instance: MagicMock = MagicMock()
    mock_s3_read_write_instance.get_document_from_s3 = mock_get_document_from_s3
    mock_s3_read_write.return_value = mock_s3_read_write_instance

    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    document_upload: DocumentUpload = DocumentUpload.objects.create(
        base_case=simplified_case,
        uploaded_by=user,
        name=UPLOAD_FILE_NAME,
    )
    path_kwargs: dict[str, int] = {"pk": document_upload.id}

    response: HttpResponse = admin_client.get(
        reverse("cases:document-upload-download", kwargs=path_kwargs),
    )

    assert response.status_code == 200

    assert response.getvalue().decode() == UPLOAD_FILE_CONTENT
