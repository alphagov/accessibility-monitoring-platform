from .models import ReportFeedback
from django import forms
from accessibility_monitoring_platform.apps.common.forms import (
    AMPCharField,
)


class ReportFeedbackForm(forms.ModelForm):
    what_were_you_trying_to_do = AMPCharField(
        label="What were you trying to do?",
    )
    what_went_wrong = AMPCharField(
        label="What went wrong?",
    )

    class Meta:
        model = ReportFeedback
        fields = [
            "what_were_you_trying_to_do",
            "what_went_wrong",
        ]
