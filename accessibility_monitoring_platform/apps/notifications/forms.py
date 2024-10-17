"""
Forms - reminders
"""

from django import forms

from ..common.forms import AMPDateField, AMPDateWidget, AMPTextField
from .models import Task


class ReminderForm(forms.ModelForm):
    """
    Form for Task model
    """

    date = AMPDateField(
        label="Date of reminder",
        required=True,
        widget=AMPDateWidget(attrs={"populate_with_future_dates": True}),
    )
    description = AMPTextField(label="Description", required=True)

    class Meta:
        model = Task
        fields: list[str] = [
            "date",
            "description",
        ]
