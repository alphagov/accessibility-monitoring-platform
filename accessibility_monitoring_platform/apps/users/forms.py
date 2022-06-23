"""
Form for users
"""
from typing import Any, Optional

from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from django_otp.plugins.otp_email.models import EmailDevice

from ..common.utils import checks_if_2fa_is_enabled
from ..common.forms import (
    AMPChoiceCheckboxWidget,
    AMPCharFieldWide,
    AMPPasswordField,
    AMPChoiceCheckboxField,
    AMPQAAuditorModelChoiceField,
)
from ..common.models import (
    BOOLEAN_FALSE,
    BOOLEAN_TRUE,
    BOOLEAN_CHOICES,
)
from .models import EmailInclusionList


class UserCreateForm(UserCreationForm):
    """Custom user creation/registation form"""

    first_name: AMPCharFieldWide = AMPCharFieldWide(required=True, max_length=150)
    last_name: AMPCharFieldWide = AMPCharFieldWide(required=True, max_length=150)
    email: AMPCharFieldWide = AMPCharFieldWide(
        required=True,
        max_length=150,
        help_text="You'll need this email address to sign in to your account",
    )
    email_confirm: AMPCharFieldWide = AMPCharFieldWide(
        required=True,
        max_length=150,
        label="Confirm your email address",
    )
    password1 = AMPPasswordField(
        label="Password",
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = AMPPasswordField(
        label="Password confirmation",
        strip=False,
        help_text="Enter the same password as before, for verification.",
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "email_confirm",
            "password1",
            "password2",
        ]

    def clean_email_confirm(self):
        """Ensures the email conforms and is unique"""
        email: Optional[str] = self.cleaned_data.get("email")
        email_confirm: Optional[str] = self.cleaned_data.get("email_confirm")

        try:
            EmailInclusionList.objects.get(inclusion_email=email)
        except EmailInclusionList.DoesNotExist as e:
            raise ValidationError(
                "This email is not permitted to sign up",
                code="email_is_not_permitted",
            ) from e

        try:
            User.objects.get(email=email)
            raise ValidationError(
                "This email is already registered",
                code="email_already_exists",
            )
        except User.DoesNotExist:
            pass

        if email and email_confirm and email != email_confirm:
            raise ValidationError(
                "The email fields do not match",
                code="email_mismatch",
            )
        return email_confirm


class UserUpdateForm(forms.ModelForm):
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
    password: AMPPasswordField = AMPPasswordField(
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
