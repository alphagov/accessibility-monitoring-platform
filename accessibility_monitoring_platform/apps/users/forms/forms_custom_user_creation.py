"""
Form - CustomUserCreationForm for users
"""

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from ..models import EmailInclusionList
from typing import Any


class CustomUserCreationForm(UserCreationForm):
    """ Custom user registation form """

    email: forms.CharField = forms.CharField(
        required=True,
        max_length=150,
        help_text="""You'll need this email address to sign in to your account""",
    )

    email_confirm: forms.CharField = forms.CharField(
        required=True,
        max_length=150,
        label="Confirm your email address",
    )

    first_name: forms.CharField = forms.CharField(required=True, max_length=150)

    last_name: forms.CharField = forms.CharField(required=True, max_length=150)

    class Meta(UserCreationForm.Meta):
        model = User
        additional_fields: Any = (
            "first_name",
            "last_name",
            "email",
            "email_confirm",
        )
        fields: UserCreationForm.Meta = UserCreationForm.Meta.fields + additional_fields

    def __init__(self, *args, **kwargs):
        self.request: HttpRequest = kwargs.pop("request")
        super().__init__(*args, **kwargs)
        self.fields.pop("username")

    def clean_email_confirm(self):
        """ Ensures the email conforms and is unique """
        email: str = self.cleaned_data.get("email")
        email_confirm: str = self.cleaned_data.get("email_confirm")

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
