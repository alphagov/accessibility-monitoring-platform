"""
Forms - reports
"""
from typing import List

from .models import (
    Report,
    READY_FOR_QA_CHOICES,
)

from ..common.forms import (
    VersionForm,
    AMPChoiceRadioField,
    AMPTextField,
)


class ReportMetadataUpdateForm(VersionForm):
    """
    Form for editing report metadata
    """

    ready_for_qa = AMPChoiceRadioField(
        label="Report ready for QA process?",
        choices=READY_FOR_QA_CHOICES,
        help_text="This field effects the case status",
    )
    notes = AMPTextField(label="Notes")

    class Meta:
        model = Report
        fields: List[str] = [
            "version",
            "ready_for_qa",
            "notes",
        ]
