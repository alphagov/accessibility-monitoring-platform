"""
Forms - detailed
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
from .models import Boolean, DetailedCase


class DetailedCaseCreateForm(forms.ModelForm):
    """
    Form for creating a case
    """

    organisation_name = AMPCharFieldWide(
        label="Organisation name",
    )
    parental_organisation_name = AMPCharFieldWide(label="Parent organisation name")
    home_page_url = AMPURLField(label="Full URL")
    website_name = AMPCharFieldWide(label="Website name")
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    subcategory = AMPModelChoiceField(
        label="Sub-category",
        queryset=SubCategory.objects.all(),
    )
    enforcement_body = AMPChoiceRadioField(
        label="Which equalities body will check the case?",
        choices=DetailedCase.EnforcementBody.choices,
    )
    psb_location = AMPChoiceRadioField(
        label="Public sector body location",
        choices=DetailedCase.PsbLocation.choices,
    )
    previous_case_url = AMPURLField(
        label="URL to previous case",
        help_text="If the website has been previously audited, include a link to the case below",
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
        model = DetailedCase
        fields = [
            "organisation_name",
            "parental_organisation_name",
            "home_page_url",
            "website_name",
            "sector",
            "subcategory",
            "enforcement_body",
            "psb_location",
            "previous_case_url",
            "is_complaint",
            "notes",
        ]

    def clean_home_page_url(self):
        home_page_url = self.cleaned_data.get("home_page_url")
        if not home_page_url:
            raise ValidationError("Full URL is required")
        return home_page_url

    def clean_enforcement_body(self):
        enforcement_body = self.cleaned_data.get("enforcement_body")
        if not enforcement_body:
            raise ValidationError("Choose which equalities body will check the case")
        return enforcement_body

    def clean_previous_case_url(self):
        """Check url contains case number"""
        previous_case_url = self.cleaned_data.get("previous_case_url")

        # Check if URL was entered
        if not previous_case_url:
            return previous_case_url

        # Check if URL exists
        if requests.head(previous_case_url, timeout=10).status_code >= 400:
            raise ValidationError("Previous case URL does not exist")

        # Extract case id from view case URL
        try:
            case_id: str = re.search(".*/cases/(.+?)/view/?", previous_case_url).group(  # type: ignore
                1
            )
        except AttributeError:
            raise ValidationError(  # pylint: disable=raise-missing-from
                "Previous case URL did not contain case id"
            )

        # Check if Case exists matching id from URL
        if case_id.isdigit() and DetailedCase.objects.filter(id=case_id).exists():
            return previous_case_url
        else:
            raise ValidationError("Previous case not found in platform")


class DetailedCaseMetadataUpdateForm(DetailedCaseCreateForm, VersionForm):
    case_metadata_complete_date = AMPDatePageCompleteField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sector"].empty_label = "Unknown"

    class Meta:
        model = DetailedCase
        fields = [
            "version",
            "organisation_name",
            "parental_organisation_name",
            "home_page_url",
            "website_name",
            "sector",
            "subcategory",
            "enforcement_body",
            "psb_location",
            "previous_case_url",
            "is_complaint",
            "notes",
            "case_metadata_complete_date",
        ]


class DetailedCaseSearchForm(forms.Form):
    """Form for searching for detailed cases"""

    case_search = AMPCharFieldWide(label="Search")
