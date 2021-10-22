"""
Tests for update user form - users
"""

from django.test import TestCase
from django.urls import reverse
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from typing import Optional, TypedDict
from ..models import EmailInclusionList
from ..forms import UpdateUserForm

from django.http import HttpRequest


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

    test_unregistered_email_returns_error()
        Returns an error with email not in inclusion list

    test_email_already_in_use_returns_error()
        Returns an error if email is already in use

    test_form_mismatched_email_fields_returns_error()
        Returns an error if email fields are mismatched

    test_incorrect_password_returns_error()
        Returns an error if password is incorrect
    """

    def setUp(self):
        """ Sets up the test environment with a request factory """
        self.factory: RequestFactory = RequestFactory()

    def test_form_conforms(self):
        """ Tests if form.is_valid() is working as expected """
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        user: User = User.objects.create(
            username="admin2@email.com", email="admin2@email.com"
        )
        user.set_password("12345")
        user.save()
        self.client.login(username="admin2@email.com", password="12345")

        request: HttpRequest = self.factory.get(reverse("users:account_details"))
        request.user = user

        data: FormRequestAccountDetails = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin2@email.com",
            "password": "12345",
        }

        form: UpdateUserForm = UpdateUserForm(
            data=data or None, request=request, initial={}
        )

        self.assertTrue(form.is_valid())

    def test_unregistered_email_returns_error(self):
        """ Returns an error with email not in inclusion list """
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        user: User = User.objects.create(
            username="admin2@email.com", email="admin2@email.com"
        )
        user.set_password("12345")
        user.save()
        self.client.login(username="admin2@email.com", password="12345")

        request: HttpRequest = self.factory.get(reverse("users:account_details"))
        request.user = user

        data: FormRequestAccountDetails = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "UNREGISTERED@email.com",
            "email_confirm": "UNREGISTERED@email.com",
            "password": "12345",
        }

        form: UpdateUserForm = UpdateUserForm(
            data=data or None, request=request, initial={}
        )

        self.assertEqual(
            form.errors["email_confirm"], ["This email is not permitted to sign up"]
        )

    def test_email_already_in_use_returns_error(self):
        """ Returns an error if email is already in use """
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        EmailInclusionList.objects.create(inclusion_email="OLD_EMAIL@email.com")
        user: User = User.objects.create(email="OLD_EMAIL@email.com")
        user.save()

        user: User = User.objects.create(
            username="admin2@email.com", email="admin2@email.com"
        )
        user.set_password("12345")
        user.save()

        self.client.login(username="admin2@email.com", password="12345")

        request: HttpRequest = self.factory.get(reverse("users:account_details"))
        request.user = user

        data: FormRequestAccountDetails = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "OLD_EMAIL@email.com",
            "email_confirm": "OLD_EMAIL@email.com",
            "password": "12345",
        }

        form: UpdateUserForm = UpdateUserForm(
            data=data or None, request=request, initial={}
        )

        self.assertEqual(
            form.errors["email_confirm"], ["This email is already registered"]
        )

    def test_form_mismatched_email_fields_returns_error(self):
        """ Returns an error if email fields are mismatched """
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        user: User = User.objects.create(
            username="admin2@email.com", email="admin2@email.com"
        )
        user.set_password("12345")
        user.save()
        self.client.login(username="admin2@email.com", password="12345")

        request: HttpRequest = self.factory.get(reverse("users:account_details"))
        request.user = user

        data: FormRequestAccountDetails = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin3@email.com",
            "password": "12345",
        }

        form: UpdateUserForm = UpdateUserForm(
            data=data or None, request=request, initial={}
        )

        self.assertEqual(
            form.errors["email_confirm"], ["The email fields do not match"]
        )

    def test_incorrect_password_returns_error(self):
        """ Returns an error if password is incorrect """
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        user: User = User.objects.create(
            username="admin2@email.com", email="admin2@email.com"
        )
        user.set_password("12345")
        user.save()
        self.client.login(username="admin2@email.com", password="12345")

        request: HttpRequest = self.factory.get(reverse("users:account_details"))
        request.user = user

        data: FormRequestAccountDetails = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin2@email.com",
            "password": "WRONG_PASSWORD",
        }

        form: UpdateUserForm = UpdateUserForm(
            data=data or None, request=request, initial={}
        )

        self.assertEqual(form.errors["password"], ["Password is incorrect"])
