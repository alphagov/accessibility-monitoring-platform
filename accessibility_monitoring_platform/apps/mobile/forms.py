"""
Forms - mobile
"""

import re

import requests
from django import forms
from django.core.exceptions import ValidationError

from ..common.forms import (
    AMPCharFieldWide,
    AMPChoiceCheckboxField,
    AMPChoiceCheckboxWidget,
    AMPChoiceRadioField,
    AMPDatePageCompleteField,
    AMPModelChoiceField,
    AMPTextField,
    AMPURLField,
    VersionForm,
)
from ..common.models import Sector, SubCategory
from .models import Boolean, MobileCase


class MobileCaseCreateForm(forms.ModelForm):
    """
    Form for creating a case
    """

    organisation_name = AMPCharFieldWide(
        label="Organisation name",
    )
    parental_organisation_name = AMPCharFieldWide(label="Parent organisation name")
    app_name = AMPCharFieldWide(label="App name")
    app_store_url = AMPURLField(label="App store URL")
    app_os = AMPChoiceRadioField(
        label="App OS",
        choices=MobileCase.AppOS.choices,
    )
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    subcategory = AMPModelChoiceField(
        label="Sub-category",
        queryset=SubCategory.objects.all(),
    )
    enforcement_body = AMPChoiceRadioField(
        label="Which equalities body will check the case?",
        choices=MobileCase.EnforcementBody.choices,
    )
    psb_location = AMPChoiceRadioField(
        label="Public sector body location",
        choices=MobileCase.PsbLocation.choices,
    )
    is_complaint = AMPChoiceCheckboxField(
        label="Complaint?",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Did this case originate from a complaint?"}
        ),
    )
    notes = AMPTextField(label="Notes")

    class Meta:
        model = MobileCase
        fields = [
            "organisation_name",
            "parental_organisation_name",
            "app_name",
            "app_store_url",
            "app_os",
            "sector",
            "subcategory",
            "enforcement_body",
            "psb_location",
            "is_complaint",
            "notes",
        ]

    def clean_app_store_url(self):
        app_store_url = self.cleaned_data.get("app_store_url")
        if not app_store_url:
            raise ValidationError("Full URL is required")
        return app_store_url

    def clean_enforcement_body(self):
        enforcement_body = self.cleaned_data.get("enforcement_body")
        if not enforcement_body:
            raise ValidationError("Choose which equalities body will check the case")
        return enforcement_body


class MobileCaseMetadataUpdateForm(MobileCaseCreateForm, VersionForm):
    case_metadata_complete_date = AMPDatePageCompleteField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sector"].empty_label = "Unknown"

    class Meta:
        model = MobileCase
        fields = [
            "version",
            "organisation_name",
            "parental_organisation_name",
            "app_name",
            "app_store_url",
            "app_os",
            "sector",
            "subcategory",
            "enforcement_body",
            "psb_location",
            "is_complaint",
            "notes",
            "is_complaint",
            "notes",
            "case_metadata_complete_date",
        ]


class MobileCaseSearchForm(forms.Form):
    """Form for searching for mobile cases"""

    case_search = AMPCharFieldWide(label="Search")
