"""
Forms - reminders
"""
from typing import List

from django import forms

from ..common.forms import (
    AMPTextField,
    AMPDateField,
)
from .models import Reminder


class ReminderForm(forms.ModelForm):
    """
    Form for Reminder model
    """

    due_date = AMPDateField(label="Date of reminder", required=True)
    description = AMPTextField(label="Description", required=True)

    class Meta:
        model = Reminder
        fields: List[str] = [
            "due_date",
            "description",
        ]
