"""
Forms - reports
"""

from django import forms

from ..common.forms import AMPCharFieldWide, AMPTextField
from .models import ReportWrapper


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
        fields: list[str] = [
            "title",
            "sent_by",
            "contact",
            "related_content",
        ]
