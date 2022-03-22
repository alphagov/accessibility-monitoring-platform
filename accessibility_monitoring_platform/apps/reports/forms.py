"""
Forms - reports
"""
from typing import List

from django import forms
from django.core.exceptions import ValidationError

from .models import (
    Report,
    Section,
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


class SectionUpdateForm(VersionForm):
    """
    Form for editing report section
    """

    content = AMPTextField(
        label="", widget=forms.Textarea(attrs={"class": "govuk-textarea", "rows": "20"})
    )

    def clean_content(self):
        content = self.cleaned_data["content"]
        if "<script>" in content or "</script>" in content:
            raise ValidationError("<script> tags are not allowed")
        return content

    class Meta:
        model = Section
        fields: List[str] = [
            "version",
            "content",
        ]
