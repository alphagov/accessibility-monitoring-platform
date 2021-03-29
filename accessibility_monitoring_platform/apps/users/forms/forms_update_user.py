"""
Form - UpdateUserForm for users
"""

from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from ..models import EmailInclusionList
from typing import Any


class UpdateUserForm(forms.ModelForm):
    """ Custom user update user form """

    first_name: forms.CharField = forms.CharField(
        required=True,
        max_length=150
    )

    last_name: forms.CharField = forms.CharField(
        required=True,
        max_length=150
    )

    email: forms.CharField = forms.CharField(
        required=True,
        max_length=150,
        help_text='''You'll need this email address to sign in to your account''',
    )

    email_confirm: forms.CharField = forms.CharField(
        required=True,
        max_length=150,
        label='Confirm your email address',
    )

    password: forms.CharField = forms.CharField(
        widget=forms.PasswordInput,
        help_text='Enter your password to confirm the update',
    )

    def __init__(self, *args, **kwargs):
        self.request: HttpRequest = kwargs.pop('request')
        super(UpdateUserForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'email_confirm',
            'password',
        ]

    def clean_email_confirm(self):
        """ Ensures the email conforms and is unique """
        email: str = self.cleaned_data.get('email')
        email_confirm: str = self.cleaned_data.get('email_confirm')

        try:
            EmailInclusionList.objects.get(inclusion_email=email)
        except EmailInclusionList.DoesNotExist as e:
            raise ValidationError(
                'This email is not permitted to sign up',
                code='email_is_not_permitted',
            ) from e

        try:
            req: Any = self.request
            query_set = User.objects \
                .exclude(id=req.user.id) \
                .filter(email=email)

            if query_set.first():
                raise ValidationError(
                    'This email is already registered',
                    code='email_already_exists',
                )
        except User.DoesNotExist:
            pass

        if email and email_confirm and email != email_confirm:
            raise ValidationError(
                'The email fields do not match',
                code='email_mismatch',
            )
        return email_confirm

    def clean_password(self):
        cleaned_data: Any = super(UpdateUserForm, self).clean()
        password: Any = cleaned_data.get('password')
        if self.request.user.check_password(password) is False:
            raise forms.ValidationError('Password is incorrect')
        return password
