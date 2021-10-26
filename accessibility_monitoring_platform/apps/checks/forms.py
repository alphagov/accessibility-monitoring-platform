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
    AMPChoiceCheckboxWidget,
    AMPModelChoiceField,
    AMPAuditorModelChoiceField,
    AMPCharField,
    AMPCharFieldWide,
    AMPTextField,
    AMPChoiceField,
    AMPChoiceRadioField,
    AMPChoiceCheckboxField,
    AMPDateField,
    AMPDateSentField,
    AMPDatePageCompleteField,
    AMPDateRangeForm,
    AMPURLField,
)
from .models import (
    Check,
    SCREEN_SIZE_CHOICES,
    EXEMPTION_CHOICES,
    TYPE_CHOICES,
)


class CheckCreateForm(VersionForm):
    """
    Form for creating a check
    """

    date_of_test = AMPDateField(label="Date of test")
    description = AMPCharFieldWide(label="Test description")
    screen_size = AMPChoiceField(label="Screen size", choices=SCREEN_SIZE_CHOICES)
    is_exemption = AMPChoiceRadioField(label="Exemptions?", choices=EXEMPTION_CHOICES)
    notes = AMPTextField(label="Notes")
    type = AMPChoiceRadioField(label="Initital test or equality body retest?", choices=TYPE_CHOICES)

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
        ]


class CheckUpdateMetadataForm(CheckCreateForm):
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
