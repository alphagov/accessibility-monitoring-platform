"""
Forms - reports
"""
from typing import Any, List

from django import forms

from .models import (
    Report,
    Section,
    TableRow,
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

    class Meta:
        model = Section
        fields: List[str] = [
            "version",
            "content",
        ]


class TableRowUpdateForm(forms.ModelForm):
    """
    Form for updating table row
    """

    cell_content_1 = AMPTextField(label="")
    cell_content_2 = AMPTextField(label="")

    class Meta:
        model = TableRow
        fields = [
            "cell_content_1",
            "cell_content_2",
        ]


TableRowFormset: Any = forms.modelformset_factory(
    TableRow, TableRowUpdateForm, extra=0
)
