"""
Test forms of audits app
"""

from django.core.files.uploadedfile import SimpleUploadedFile

from ..forms import StatementBackupForm, StatementCheckCreateUpdateForm
from ..models import StatementCheck

DOCUMENT_NAME: str = "document.txt"
DOCUMENT_CONTENT: str = "Document content"


def test_statement_overview_not_in_type_choices():
    """Tests statement overview has been removed from type choices"""

    form: StatementCheckCreateUpdateForm = StatementCheckCreateUpdateForm()

    assert len(form.fields["type"].choices) == len(StatementCheck.Type.choices) - 1
    assert StatementCheck.Type.OVERVIEW not in [
        value for value, _ in form.fields["type"].choices
    ]


def test_clean_statement_backup_form_file_to_upload():
    """Tests file upload size validation"""
    form: StatementBackupForm = StatementBackupForm(
        {
            "type": "statement",
        },
        {
            "file_to_upload": SimpleUploadedFile(
                DOCUMENT_NAME, DOCUMENT_CONTENT.encode()
            ),
        },
    )

    assert form.is_valid()
