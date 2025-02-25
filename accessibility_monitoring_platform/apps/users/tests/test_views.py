"""
Tests for users views
"""

from typing import TypedDict

import pytest
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse
from django_otp.plugins.otp_email.models import EmailDevice
from pytest_django.asserts import assertContains

from ...notifications.models import NotificationSetting
from ..models import AllowedEmail
from .test_forms import UserCreateFormData

FIRST_NAME: str = "Joe"
LAST_NAME: str = "Bloggs"
VALID_USER_EMAIL: str = "valid@example.com"
INVALID_USER_EMAIL: str = "invalid@example.com"
VALID_PASSWORD: str = "12345"
INVALID_PASSWORD: str = "WRONG"
VALID_USER_CREATE_FORM_DATA: UserCreateFormData = {
    "first_name": FIRST_NAME,
    "last_name": LAST_NAME,
    "email": VALID_USER_EMAIL,
    "email_confirm": VALID_USER_EMAIL,
    "password1": VALID_PASSWORD,
    "password2": VALID_PASSWORD,
}
EMAIL_NOTIFICATIONS: str = "on"
ENABLE_2FA: str = "yes"


class UserUpdateFormData(TypedDict):
    enable_2fa: str
    first_name: str
    last_name: str
    password: str


VALID_USER_UPDATE_FORM_DATA: UserUpdateFormData = {
    "enable_2fa": ENABLE_2FA,
    "first_name": FIRST_NAME,
    "last_name": LAST_NAME,
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
def test_register_loads_correctly_no_auth(client):
    """Tests if register page loads correctly"""
    response: HttpResponse = client.get(reverse("users:register"))

    assert response.status_code == 200
    assertContains(response, "Fill in the form below to create an account")


def test_register_redirects_with_auth(admin_client):
    """Tests if register redirects when logged in"""
    response: HttpResponse = admin_client.get(
        path=reverse("users:register"), follow=True
    )

    assert response.status_code == 200
    assertContains(
        response,
        """<h1 class="govuk-heading-xl amp-margin-bottom-10">Your cases</h1>""",
        html=True,
    )


@pytest.mark.django_db
def test_register_post_redirects(client):
    """Tests if register redirects to dashboard after post request"""
    AllowedEmail.objects.create(inclusion_email=VALID_USER_EMAIL)

    response: HttpResponse = client.post(
        reverse("users:register"), data=VALID_USER_CREATE_FORM_DATA, follow=True
    )

    assert response.status_code == 200
    assertContains(response, "Your cases")


@pytest.mark.django_db
def test_register_post_saves_correctly(client):
    """Tests if register saves to the database correctly"""
    AllowedEmail.objects.create(inclusion_email=VALID_USER_EMAIL)

    response: HttpResponse = client.post(
        reverse("users:register"), data=VALID_USER_CREATE_FORM_DATA, follow=True
    )

    assert response.status_code == 200

    user: User = User.objects.get(email=VALID_USER_EMAIL)

    assert user.first_name == FIRST_NAME
    assert user.last_name == LAST_NAME
    assert user.email == VALID_USER_EMAIL
    assert user.username == VALID_USER_EMAIL

    notificiation_setting: NotificationSetting = NotificationSetting.objects.get(
        user=user
    )

    assert notificiation_setting.email_notifications_enabled


@pytest.mark.django_db
def test_register_post_errors_appear(client):
    """Tests if error message appears if there is a mistake in the form"""
    data: UserCreateFormData = VALID_USER_CREATE_FORM_DATA.copy()

    response: HttpResponse = client.post(
        reverse("users:register"), data=data, follow=True
    )

    assert response.status_code == 200
    assertContains(response, "This email is not permitted to sign up")


@pytest.mark.django_db
def test_edit_user_loads_correctly_with_auth(client):
    """Tests if a user is logged in and can access account details"""
    user: User = create_user()
    client.login(username=VALID_USER_EMAIL, password=VALID_PASSWORD)

    response: HttpResponse = client.get(
        reverse("users:edit-user", kwargs={"pk": user.id})
    )

    assert response.status_code == 200
    assert str(response.context["user"]) == VALID_USER_EMAIL
    assertContains(response, "Account details")


@pytest.mark.django_db
def test_edit_user_returns_403_for_other_users(client):
    """Tests logged user cannot edit other account details"""
    create_user()
    client.login(username=VALID_USER_EMAIL, password=VALID_PASSWORD)
    other_user: User = User.objects.create()

    response: HttpResponse = client.get(
        reverse("users:edit-user", kwargs={"pk": other_user.id})
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_edit_user_loads_correctly_no_auth(client):
    """Tests if a unauthenticated user returns a 302 response"""
    user: User = create_user()
    url: str = reverse("users:edit-user", kwargs={"pk": user.id})

    response: HttpResponse = client.get(url)

    assert response.status_code == 302
    assert response.url == f"/account/login/?next={url}"


@pytest.mark.django_db
def test_edit_user_post_saves_correctly(client):
    """Tests if form saves correctly and show success message"""
    AllowedEmail.objects.create(inclusion_email=VALID_USER_EMAIL)
    user: User = create_user()
    client.login(username=VALID_USER_EMAIL, password=VALID_PASSWORD)

    data: UserUpdateFormData = VALID_USER_UPDATE_FORM_DATA.copy()
    response: HttpResponse = client.post(
        reverse("users:edit-user", kwargs={"pk": user.id}),
        data=data,
        follow=True,
    )

    assert response.status_code == 200
    assertContains(response, "Account details")

    updated_user: User = User.objects.get(email=VALID_USER_EMAIL)

    assert updated_user.first_name == FIRST_NAME
    assert updated_user.last_name == LAST_NAME

    messages: list[str] = [str(x) for x in list(response.context["messages"])]
    assert messages[0] == "Successfully saved details!"

    notificiation_setting: NotificationSetting = NotificationSetting.objects.get(
        user=user
    )

    assert not notificiation_setting.email_notifications_enabled

    email_device: EmailDevice = EmailDevice.objects.get(user=user, name="default")

    assert email_device.confirmed


@pytest.mark.django_db
def test_edit_user_post_errors_appear(client):
    """Tests if error message appears if there is a mistake in the form"""
    AllowedEmail.objects.create(inclusion_email=VALID_USER_EMAIL)
    user: User = create_user()
    client.login(username=VALID_USER_EMAIL, password=VALID_PASSWORD)

    data: UserUpdateFormData = VALID_USER_UPDATE_FORM_DATA.copy()
    data["password"] = INVALID_PASSWORD

    response: HttpResponse = client.post(
        reverse("users:edit-user", kwargs={"pk": user.id}),
        data=data,
        follow=True,
    )

    assert response.status_code == 200
    assertContains(response, "Password is incorrect")


@pytest.mark.django_db
def test_2fa_not_enabled_on_user_creation(client):
    """Tests to see if 2FA EmailDevice not created when user is registered"""
    AllowedEmail.objects.create(inclusion_email=VALID_USER_EMAIL)

    response: HttpResponse = client.post(
        reverse("users:register"), data=VALID_USER_CREATE_FORM_DATA, follow=True
    )

    assert response.status_code == 200

    user: User = User.objects.get(email=VALID_USER_EMAIL)

    assert not EmailDevice.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_2fa_not_enabled_on_user_update(client):
    """Test user can be updated and not enable 2FA"""
    user: User = create_user()
    client.login(username=VALID_USER_EMAIL, password=VALID_PASSWORD)

    data: dict[str, str] = VALID_USER_UPDATE_FORM_DATA.copy()
    del data["enable_2fa"]

    response: HttpResponse = client.post(
        reverse("users:edit-user", kwargs={"pk": user.id}),
        data=data,
        follow=True,
    )

    assert response.status_code == 200

    email_device: EmailDevice = EmailDevice.objects.get(user=user, name="default")

    assert not email_device.confirmed


@pytest.mark.django_db
def test_user_with_2fa_emailed_token_to_login(client, mailoutbox):
    """Test user with 2FA can login with emailed token"""
    user: User = create_user()
    EmailDevice.objects.create(user=user, name="default", confirmed=True)

    url: str = reverse("dashboard:home")

    response = client.get(url)

    assert response.status_code == 302
    assert response.url == f"/account/login/?next={url}"

    auth_data: dict[str, str] = {
        "auth-username": VALID_USER_EMAIL,
        "auth-password": VALID_PASSWORD,
        "login_view-current_step": "auth",
    }

    response = client.post("/account/login/", data=auth_data, follow=True)

    assert response.status_code == 200
    assertContains(response, "Token")

    user = auth.get_user(client)
    assert not user.is_authenticated

    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == settings.OTP_EMAIL_SUBJECT
    assert len(mailoutbox[0].body) == 7

    token_data: dict[str, str | int] = {
        "token-otp_token": mailoutbox[0].body.strip(),
        "login_view-current_step": "token",
    }

    response = client.post("/account/login/", data=token_data, follow=True)

    assert response.status_code == 200

    user = auth.get_user(client)
    assert user.is_authenticated
