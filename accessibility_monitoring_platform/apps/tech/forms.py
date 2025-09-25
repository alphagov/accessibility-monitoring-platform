"""Forms for tech team app"""

import logging

from django import forms

from ..common.forms import (
    AMPCharFieldWide,
    AMPChoiceCheckboxField,
    AMPChoiceCheckboxWidget,
    AMPChoiceField,
    AMPTextField,
)
from ..common.models import Boolean

LOG_LEVEL_CHOICES: list[tuple[int, str]] = [
    (logging.WARNING, "Warning"),
    (logging.ERROR, "Error"),
    (logging.CRITICAL, "Critical"),
]
IMPORT_MODEL_CHOICES: list[tuple[int, str]] = [
    ("detailed", "Detailed testing case"),
    ("mobile", "Mobile testing case"),
]

logger = logging.getLogger(__name__)


class PlatformCheckingForm(forms.Form):
    """Form used to write a log message"""

    level = AMPChoiceField(label="Level", choices=LOG_LEVEL_CHOICES)
    message = AMPCharFieldWide(label="Message", initial="Test log message")


class ImportCSVForm(forms.Form):
    data = AMPTextField(label="CSV data")


class ImportTrelloCommentsForm(forms.Form):
    data = AMPTextField(label="CSV data")
    reset_data = AMPChoiceCheckboxField(
        label="Reset existing data",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(attrs={"label": "Delete existing data"}),
    )
