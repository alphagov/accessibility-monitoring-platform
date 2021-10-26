"""
Forms - checks (called tests by users)
"""
from typing import Any, List, Tuple

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from ..common.forms import (
    VersionForm,
    AMPCharFieldWide,
    AMPTextField,
    AMPChoiceField,
    AMPChoiceRadioField,
    AMPChoiceCheckboxField,
    AMPDateField,
    AMPDatePageCompleteField,
    AMPURLField,
)
from .models import (
    Check,
    Page,
    SCREEN_SIZE_CHOICES,
    EXEMPTION_CHOICES,
    CHECK_TYPE_CHOICES,
)


class CheckCreateForm(forms.ModelForm):
    """
    Form for creating a check
    """

    date_of_test = AMPDateField(label="Date of test")
    description = AMPCharFieldWide(label="Test description")
    screen_size = AMPChoiceField(label="Screen size", choices=SCREEN_SIZE_CHOICES)
    is_exemption = AMPChoiceRadioField(label="Exemptions?", choices=EXEMPTION_CHOICES)
    notes = AMPTextField(label="Notes")
    type = AMPChoiceRadioField(
        label="Initital test or equality body retest?", choices=CHECK_TYPE_CHOICES
    )

    class Meta:
        model = Check
        fields: List[str] = [
            "date_of_test",
            "description",
            "screen_size",
            "is_exemption",
            "notes",
            "type",
        ]


class CheckUpdateMetadataForm(CheckCreateForm, VersionForm):
    """
    Form for editing check metadata
    """

    check_metadata_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Check
        fields: List[str] = [
            "version",
            "date_of_test",
            "description",
            "screen_size",
            "is_exemption",
            "notes",
            "type",
            "check_metadata_complete_date",
        ]


class CheckPageUpdateForm(forms.ModelForm):
    """
    Form for updating a page
    """

    name = AMPCharFieldWide(label="Page name")
    url = AMPURLField(label="URL")
    not_found = AMPChoiceCheckboxField(label="Not found?")

    class Meta:
        model = Page
        fields = [
            "name",
            "url",
            "not_found",
        ]


CheckPageFormset: Any = forms.modelformset_factory(
    Page, CheckPageUpdateForm, extra=0
)
CheckPageFormsetOneExtra: Any = forms.modelformset_factory(
    Page, CheckPageUpdateForm, extra=1
)

class CheckUpdatePagesForm(VersionForm):
    """
    Form for editing check pages page
    """

    check_pages_complete_date = AMPDatePageCompleteField()

    class Meta:
        model = Check
        fields: List[str] = [
            "version",
            "check_pages_complete_date",
        ]
