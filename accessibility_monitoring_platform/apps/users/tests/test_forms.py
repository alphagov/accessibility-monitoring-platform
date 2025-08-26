"""
Tests for users forms
"""

from typing import TypedDict

import pytest
from django.contrib.auth.models import User

from ..forms import UserCreateForm, UserUpdateForm
from ..models import AllowedEmail

VALID_USER_EMAIL: str = "valid@example.com"
INVALID_USER_EMAIL: str = "invalid@example.com"
VALID_PASSWORD: str = "12345"
INVALID_PASSWORD: str = "wrong_password"


class UserCreateFormData(TypedDict):
    first_name: str
    last_name: str
    email: str
    email_confirm: str
    password1: str
    password2: str


class UserUpdateFormData(TypedDict):
    email_notifications: str
    enable_2fa: str
    first_name: str
    last_name: str
    password: str


VALID_USER_CREATE_FORM_DATA: UserCreateFormData = {
    "first_name": "Joe",
    "last_name": "Blogs",
    "email": VALID_USER_EMAIL,
    "email_confirm": VALID_USER_EMAIL,
    "password1": VALID_PASSWORD,
    "password2": VALID_PASSWORD,
}
VALID_USER_UPDATE_FORM_DATA: UserUpdateFormData = {
    "email_notifications": "no",
    "enable_2fa": "no",
    "first_name": "Joe",
    "last_name": "Blogs",
    "password": VALID_PASSWORD,
}


def create_user() -> User:
    """Create valid user"""
    AllowedEmail.objects.create(inclusion_email=VALID_USER_EMAIL)
    user: User = User.objects.create(
        username=VALID_USER_EMAIL,
        email=VALID_USER_EMAIL,
    )
    user.set_password(VALID_PASSWORD)
    user.save()
    return user


@pytest.mark.django_db
def test_valid_user_create_form():
    """Tests if form.is_valid() is working as expected"""
    AllowedEmail.objects.create(inclusion_email=VALID_USER_EMAIL)

    form: UserCreateForm = UserCreateForm(data=VALID_USER_CREATE_FORM_DATA)

    assert form.is_valid()


@pytest.mark.django_db
def test_form_email_not_in_inclusion_list():
    """Returns an error with email not in inclusion list"""
    data: UserCreateFormData = VALID_USER_CREATE_FORM_DATA.copy()
    data["email"] = INVALID_USER_EMAIL
    data["email_confirm"] = INVALID_USER_EMAIL

    form: UserCreateForm = UserCreateForm(data=data)

    assert form.errors["email_confirm"] == ["This email is not permitted to sign up"]


@pytest.mark.django_db
def test_form_email_already_registered_error():
    """Returns an error if email is already registered"""
    AllowedEmail.objects.create(inclusion_email=VALID_USER_EMAIL)
    User.objects.create(username=VALID_USER_EMAIL, email=VALID_USER_EMAIL)

    form: UserCreateForm = UserCreateForm(data=VALID_USER_CREATE_FORM_DATA)

    assert form.errors["email_confirm"] == ["This email is already registered"]


@pytest.mark.django_db
def test_form_emails_do_not_match():
    """Returns an error if emails do not match"""
    AllowedEmail.objects.create(inclusion_email=VALID_USER_EMAIL)
    data: UserCreateFormData = VALID_USER_CREATE_FORM_DATA.copy()
    data["email_confirm"] = INVALID_USER_EMAIL

    form: UserCreateForm = UserCreateForm(data=data)

    assert form.errors["email_confirm"] == ["The email fields do not match"]


@pytest.mark.django_db
def test_valid_user_update_form():
    """Tests if form.is_valid() is working as expected"""
    user: User = create_user()

    form: UserUpdateForm = UserUpdateForm(
        data=VALID_USER_UPDATE_FORM_DATA,
        user=user,
    )

    assert form.is_valid()
