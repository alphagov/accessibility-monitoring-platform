"""Forms for exports"""

from django import forms
from django.core.exceptions import ValidationError

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

    def clean_cutoff_date(self):
        cutoff_date = self.cleaned_data["cutoff_date"]
        if Export.objects.filter(cutoff_date=cutoff_date).exists():
            raise ValidationError("Export for this date already exists")
        return cutoff_date


class ExportConfirmForm(forms.ModelForm):
    """
    Form for confiriming an export
    """

    cutoff_date = forms.DateField(widget=forms.HiddenInput())

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
