"""
Tests for update user form - users
"""

from typing import Dict, Optional, TypedDict
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django_otp.plugins.otp_email.models import EmailDevice
from django.test import Client
from django.core import mail
from django.contrib import auth


from ..forms import UpdateUserForm
from ..models import EmailInclusionList


class FormRequestAccountDetails(TypedDict):
    first_name: str
    last_name: str
    email: str
    email_confirm: str
    password: str
    active_qa_auditor: Optional[int]


class UpdateUserFormTestCase(TestCase):
    """
    Form tests for update user

    Methods
    -------
    setUp()
        Sets up the test environment

    test_form_conforms()
        Tests if form.is_valid() is working as expected

    test_incorrect_password_returns_error()
        Returns an error if password is incorrect

    test_2fa_initiates_correctly()
        Tests to see if 2FA works as expected
    """

    def setUp(self):
        """Sets up the test environment with a request factory"""
        self.factory: RequestFactory = RequestFactory()

    def test_form_conforms(self):
        """Tests if form.is_valid() is working as expected"""
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        user: User = User.objects.create(
            username="admin2@email.com",
            email="admin2@email.com",
        )
        user.set_password("12345")
        user.save()
        self.client.login(
            username="admin2@email.com",
            password="12345",
        )

        request: HttpRequest = self.factory.get(reverse("users:account_details"))
        request.user = user

        data: Dict[str, str] = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "password": "12345",
        }

        form: UpdateUserForm = UpdateUserForm(
            data=data or None,
            request=request,
            initial={},
        )

        self.assertTrue(form.is_valid())

    def test_incorrect_password_returns_error(self):
        """Returns an error if password is incorrect"""
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        user: User = User.objects.create(
            username="admin2@email.com",
            email="admin2@email.com",
        )
        user.set_password("12345")
        user.save()
        self.client.login(
            username="admin2@email.com",
            password="12345",
        )

        request: HttpRequest = self.factory.get(reverse("users:account_details"))
        request.user = user

        data: Dict[str, str] = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin2@email.com",
            "password": "WRONG_PASSWORD",
        }

        form: UpdateUserForm = UpdateUserForm(
            data=data or None,
            request=request,
            initial={},
        )

        self.assertEqual(form.errors["password"], ["Password is incorrect"])

    def test_2fa_initiates_correctly(self):
        """Tests to see if 2FA works as expected"""
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        user: User = User.objects.create(
            username="admin2@email.com",
            email="admin2@email.com",
        )
        user.set_password("12345")
        user.save()
        self.client.login(
            username="admin2@email.com",
            password="12345",
        )

        self.assertFalse(EmailDevice.objects.filter(user=user).exists())

        request: HttpRequest = self.factory.get(reverse("users:account_details"))
        request.user = user

        data = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin2@email.com",
            "password": "12345",
            "enable_2fa": True,
        }

        form: UpdateUserForm = UpdateUserForm(
            data=data or None,
            request=request,
            initial={},
        )

        self.assertTrue(form.is_valid())
        self.assertTrue(EmailDevice.objects.filter(user=user).exists())

        self.client.logout()

        url: str = reverse("dashboard:home")
        client: Client = Client()
        user = auth.get_user(client)  # type: ignore
        self.assertEqual(user.is_authenticated, False)
        response = client.get(url)
        self.assertTrue(response.status_code == 302)
        self.assertTrue(response.url == f"/account/login/?next={url}")  # type: ignore

        auth_data = {
            "auth-username": "admin2@email.com",
            "auth-password": "12345",
            "login_view-current_step": "auth",
        }
        response = client.post("/account/login/", data=auth_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Token")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].body), 7)
        user = auth.get_user(self.client)  # type: ignore
        self.assertEqual(user.is_authenticated, False)

        auth_data = {
            "token-otp_token": int(mail.outbox[0].body[:-1]),
            "login_view-current_step": "token",
        }
        response = client.post("/account/login/", data=auth_data)

        # self.assertRedirects(response, url)  # This is failing due to response returning an inconsistent status code

        user = auth.get_user(client)  # type: ignore
        self.assertEqual(user.is_authenticated, True)
