"""Forms for exports"""

from django import forms

from ..common.forms import AMPBooleanCheckboxWidget, AMPDateField
from .models import Export


class ExportCreateForm(forms.ModelForm):
    """
    Form for creating an export
    """

    cutoff_date = AMPDateField(label="Cutoff date")

    class Meta:
        model = Export
        fields = ["cutoff_date"]


class ExportDeleteForm(forms.ModelForm):
    """
    Form for deleting an export
    """

    is_deleted = forms.BooleanField(
        required=False,
        widget=AMPBooleanCheckboxWidget(
            attrs={"label": "Confirm you want to delete the export"}
        ),
    )

    class Meta:
        model = Export
        fields = ["is_deleted"]
