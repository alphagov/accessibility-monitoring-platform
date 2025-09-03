"""
Form for users
"""

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from ..common.forms import (
    AMPCharFieldWide,
    AMPChoiceCheckboxField,
    AMPChoiceCheckboxWidget,
    AMPNewPasswordField,
)
from ..common.models import Boolean
from .models import AllowedEmail


class UserCreateForm(UserCreationForm):
    """Custom user creation/registation form"""

    first_name = AMPCharFieldWide(required=True, max_length=150)
    last_name = AMPCharFieldWide(required=True, max_length=150)
    email = AMPCharFieldWide(
        required=True,
        max_length=150,
        help_text="You'll need this email address to sign in to your account",
    )
    email_confirm = AMPCharFieldWide(
        required=True,
        max_length=150,
        label="Confirm your email address",
    )
    password1 = AMPNewPasswordField(
        label="Password",
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = AMPNewPasswordField(
        label="Password confirmation",
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
        email: str | None = self.cleaned_data.get("email")
        email_confirm: str | None = self.cleaned_data.get("email_confirm")

        try:
            AllowedEmail.objects.get(inclusion_email=email)
        except AllowedEmail.DoesNotExist as e:
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

    email_notifications = AMPChoiceCheckboxField(
        label="Enable email notifications?",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Mark the checkbox to enable email notifications"}
        ),
    )
    enable_2fa = AMPChoiceCheckboxField(
        label="Enable two-factor authentication?",
        choices=Boolean.choices,
        widget=AMPChoiceCheckboxWidget(
            attrs={"label": "Mark the checkbox to enable two-factor authentication"}
        ),
    )
    first_name = AMPCharFieldWide(required=True, max_length=150)
    last_name = AMPCharFieldWide(required=True, max_length=150)

    class Meta:
        model = User
        fields = [
            "email_notifications",
            "enable_2fa",
            "first_name",
            "last_name",
        ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
