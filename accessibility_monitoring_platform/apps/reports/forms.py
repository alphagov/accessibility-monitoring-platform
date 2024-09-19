"""
Forms - reports
"""

from typing import List

from django import forms

from ..common.forms import AMPCharFieldWide, AMPTextField, VersionForm
from .models import Report, ReportWrapper


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
