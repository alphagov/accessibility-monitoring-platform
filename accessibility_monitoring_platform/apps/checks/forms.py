"""
Forms - checks (called tests by users)
"""
from typing import Any, List

from django import forms
from django.db.models import QuerySet

from ..common.forms import (
    VersionForm,
    AMPCharFieldWide,
    AMPTextField,
    AMPChoiceField,
    AMPChoiceRadioField,
    AMPChoiceCheckboxField,
    AMPChoiceCheckboxWidget,
    AMPDateField,
    AMPDatePageCompleteField,
    AMPURLField,
)
from ..cases.models import BOOLEAN_CHOICES
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


class CheckExtraPageUpdateForm(forms.ModelForm):
    """
    Form for updating an extra page
    """

    name = AMPCharFieldWide(label="Page name")
    url = AMPURLField(label="URL")

    class Meta:
        model = Page
        fields = [
            "name",
            "url",
        ]


class CheckStandardPageUpdateForm(CheckExtraPageUpdateForm):
    """
    Form for updating a standard page (one of the 5 types of page in every check)
    """

    not_found = AMPChoiceCheckboxField(label="Not found?")
    not_found = AMPChoiceCheckboxField(
        label="Not found?",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(),
    )

    class Meta:
        model = Page
        fields = [
            "name",
            "url",
            "not_found",
        ]


CheckStandardPageFormset: Any = forms.modelformset_factory(
    Page, CheckStandardPageUpdateForm, extra=0
)
CheckExtraPageFormset: Any = forms.modelformset_factory(
    Page, CheckExtraPageUpdateForm, extra=0
)
CheckExtraPageFormsetOneExtra: Any = forms.modelformset_factory(
    Page, CheckExtraPageUpdateForm, extra=1
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
