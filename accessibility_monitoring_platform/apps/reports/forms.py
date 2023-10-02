"""
Forms - reports
"""
from typing import List

from django import forms

from .models import (
    Report,
    ReportWrapper,
)

from ..common.forms import (
    VersionForm,
    AMPCharFieldWide,
    AMPTextField,
)


class ReportNotesUpdateForm(VersionForm):
    """
    Form for editing report notes
    """

    notes = AMPTextField(label="Notes")

    class Meta:
        model = Report
        fields: List[str] = [
            "version",
            "notes",
        ]


class ReportWrapperUpdateForm(forms.ModelForm):
    """
    Form for editing report wrapper text
    """

    title = AMPCharFieldWide(label="Title")
    sent_by = AMPCharFieldWide(label="From (leave blank to hide)")
    contact = AMPCharFieldWide(label="Contact (leave blank to hide)")
    related_content = AMPTextField(label="Related content")

    class Meta:
        model = ReportWrapper
        fields: List[str] = [
            "title",
            "sent_by",
            "contact",
            "related_content",
        ]
