"""Forms for exports"""

from django import forms
from django.core.exceptions import ValidationError

from ..cases.models import Case, CaseStatus
from ..common.forms import AMPBooleanCheckboxWidget, AMPDateField
from .models import Export
from .utils import get_exportable_cases


class ExportCreateForm(forms.ModelForm):
    """
    Form for creating an export
    """

    enforcement_body = forms.CharField(widget=forms.HiddenInput())
    cutoff_date = AMPDateField(label="Cutoff date")

    class Meta:
        model = Export
        fields = ["enforcement_body", "cutoff_date"]

    def clean_cutoff_date(self):
        cutoff_date = self.cleaned_data["cutoff_date"]
        if Export.objects.filter(cutoff_date=cutoff_date, is_deleted=False).exists():
            raise ValidationError("Export for this date already exists")
        if not get_exportable_cases(
            cutoff_date=cutoff_date,
            enforcement_body=self.cleaned_data["enforcement_body"],
        ):
            raise ValidationError("There are no cases to export")
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
