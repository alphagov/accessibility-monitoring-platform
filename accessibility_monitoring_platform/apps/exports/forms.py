"""Forms for exports"""

from django import forms

from ..common.forms import AMPDateField
from .models import Export


class ExportCreateForm(forms.ModelForm):
    """
    Form for creating an export
    """

    cutoff_date = AMPDateField(label="Cutoff date")

    class Meta:
        model = Export
        fields = ["cutoff_date"]
