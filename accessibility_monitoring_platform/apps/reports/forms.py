"""
Forms - reports
"""
from typing import Any, Mapping, List, Optional

from django import forms

from .models import (
    Report,
    Section,
    TableRow,
    READY_FOR_QA_CHOICES,
    TEMPLATE_TYPE_HTML,
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

    template_type = forms.CharField(widget=forms.HiddenInput())
    content = AMPTextField(
        label="", widget=forms.Textarea(attrs={"class": "govuk-textarea", "rows": "20"})
    )

    def clean(self):
        """Check HTML content has no script tags."""
        cleaned_data: Optional[Mapping[str, Any]] = super().clean()
        if cleaned_data:
            template_type: str = cleaned_data["template_type"]
            if template_type == TEMPLATE_TYPE_HTML:
                content: str = cleaned_data["content"]
                if "<script>" in content or "</script>" in content:
                    self.add_error(
                        "content",
                        "<script> tags are not allowed",
                    )
        return cleaned_data

    class Meta:
        model = Section
        fields: List[str] = [
            "version",
            "template_type",
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


TableRowFormset: Any = forms.modelformset_factory(TableRow, TableRowUpdateForm, extra=0)
TableRowFormsetOneExtra: Any = forms.modelformset_factory(
    TableRow, TableRowUpdateForm, extra=1
)
