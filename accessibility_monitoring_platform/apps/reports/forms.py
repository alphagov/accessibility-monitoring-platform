"""
Forms - reports
"""
from typing import Any, Mapping, List, Optional

from django import forms

from .models import (
    Report,
    Section,
    TableRow,
    TEMPLATE_TYPE_HTML,
    ReportWrapper,
    ReportFeedback,
)

from ..common.forms import (
    VersionForm,
    AMPCharFieldWide,
    AMPTextField,
)


class ReportMetadataUpdateForm(VersionForm):
    """
    Form for editing report metadata
    """

    notes = AMPTextField(label="Notes")

    class Meta:
        model = Report
        fields: List[str] = [
            "version",
            "notes",
        ]


class SectionUpdateForm(VersionForm):
    """
    Form for editing report section
    """

    template_type = forms.CharField(widget=forms.HiddenInput())
    content = AMPTextField(
        label="Edit report content",
        widget=forms.Textarea(attrs={"class": "govuk-textarea", "rows": "20"}),
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


class ReportFeedbackForm(forms.ModelForm):
    """
    Form for submitting feedback
    """

    what_were_you_trying_to_do = AMPTextField(
        label="What were you trying to do?",
    )
    what_went_wrong = AMPTextField(
        label="What went wrong?",
    )

    class Meta:
        model = ReportFeedback
        fields = [
            "what_were_you_trying_to_do",
            "what_went_wrong",
        ]
