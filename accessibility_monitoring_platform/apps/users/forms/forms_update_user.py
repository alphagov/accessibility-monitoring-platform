"""
Form - UpdateUserForm for users
"""
from django.contrib.auth.models import User
from django import forms
from django.http import HttpRequest
from django_otp.plugins.otp_email.models import EmailDevice
from typing import Any
from ...common.utils import checks_if_2fa_is_enabled
from ...common.forms import (
    AMPChoiceCheckboxWidget,
    AMPCharFieldWide,
    AMPChoiceCheckboxField,
    AMPQAAuditorModelChoiceField,
)
from ...common.models import (
    BOOLEAN_FALSE,
    BOOLEAN_TRUE,
    BOOLEAN_CHOICES,
)


class UpdateUserForm(forms.ModelForm):
    """Custom user update user form"""

    active_qa_auditor: AMPQAAuditorModelChoiceField = AMPQAAuditorModelChoiceField(
        label="Active QA auditor"
    )
    email_notifications: AMPChoiceCheckboxField = AMPChoiceCheckboxField(
        label="Enable email notifications?",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Mark the checkbox to enable email notifications"}
        ),
    )
    enable_2fa: AMPChoiceCheckboxField = AMPChoiceCheckboxField(
        label="Enable two-factor authentication?",
        choices=BOOLEAN_CHOICES,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Mark the checkbox to enable two-factor authentication"}
        ),
    )
    first_name: AMPCharFieldWide = AMPCharFieldWide(required=True, max_length=150)
    last_name: AMPCharFieldWide = AMPCharFieldWide(required=True, max_length=150)
    password: forms.CharField = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Enter your password to confirm the update",
    )

    def __init__(self, *args, **kwargs):
        self.request: HttpRequest = kwargs.pop("request")
        super().__init__(*args, **kwargs)
        if checks_if_2fa_is_enabled(self.request):
            self.fields["enable_2fa"].initial = BOOLEAN_TRUE
        else:
            self.fields["enable_2fa"].initial = BOOLEAN_FALSE

    class Meta:
        model = User
        fields = [
            "active_qa_auditor",
            "email_notifications",
            "enable_2fa",
            "first_name",
            "last_name",
            "password",
        ]

    def clean_password(self):
        cleaned_data: Any = super().clean()
        password: Any = cleaned_data.get("password")
        if self.request.user.check_password(password) is False:
            raise forms.ValidationError("Password is incorrect")
        return password

    def clean_enable_2fa(self):
        enable_2fa = self.cleaned_data.get("enable_2fa")
        if enable_2fa == BOOLEAN_TRUE:
            if EmailDevice.objects.filter(user=self.request.user).exists() is False:
                EmailDevice.objects.create(
                    user=self.request.user,
                    name="default",
                    confirmed=True,
                )

            if EmailDevice.objects.get(user=self.request.user).confirmed is False:
                email_device: EmailDevice = EmailDevice.objects.get(
                    user=self.request.user
                )
                email_device.confirmed = True
                email_device.save()
            return enable_2fa
        else:
            if EmailDevice.objects.filter(user=self.request.user).exists() is False:
                return enable_2fa

            email_device: EmailDevice = EmailDevice.objects.get(user=self.request.user)
            if email_device.confirmed is True:
                email_device.confirmed = False
                email_device.save()

            return enable_2fa
