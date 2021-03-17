from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from .models import EmailInclusionList


class CustomUserCreationForm(UserCreationForm):
    email = forms.CharField(
        required=True,
        max_length=150,
        help_text='''You'll need this email address to sign in to your account''',
    )
    email_confirm = forms.CharField(
        required=True,
        max_length=150,
        label='',
        help_text='Confirm your email address'
    )
    first_name = forms.CharField(required=True, max_length=150)
    last_name = forms.CharField(required=True, max_length=150)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + (
            'first_name',
            'last_name',
            'email',
            'email_confirm',
        )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.fields.pop('username')

    def clean_email_confirm(self):
        email = self.cleaned_data.get('email')
        email_confirm = self.cleaned_data.get('email_confirm')

        try:
            EmailInclusionList.objects.get(inclusion_email=email)
        except EmailInclusionList.DoesNotExist as e:
            raise ValidationError(
                'This email is not permitted to sign up',
                code='email_is_not_permitted',
            ) from e

        try:
            User.objects.get(email=email)
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


class UpdateUser(forms.ModelForm):
    first_name = forms.CharField(
        required=True,
        max_length=150
    )
    last_name = forms.CharField(
        required=True,
        max_length=150
    )
    email = forms.CharField(
        required=True,
        max_length=150,
        help_text='''You'll need this email address to sign in to your account''',
    )
    email_confirm = forms.CharField(
        required=True,
        max_length=150,
        label='',
        help_text='Confirm your email address'
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text='Enter your password to confirm the update',
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(UpdateUser, self).__init__(*args, **kwargs)

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
        email = self.cleaned_data.get('email')
        email_confirm = self.cleaned_data.get('email_confirm')
        try:
            query_set = User.objects.exclude(
                id=self.request.user.id
            ).filter(
                email=email
            )
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
        cleaned_data = super(UpdateUser, self).clean()
        password = cleaned_data.get('password')
        if self.request.user.check_password(password) is False:
            raise forms.ValidationError(
                'Password is not correct'
            )
        return password
