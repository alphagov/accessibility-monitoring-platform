"""
Tests for user creation form - users
"""

from django.test import TestCase
from django.urls import reverse
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from typing import TypedDict
from django.http import HttpRequest
from ..models import EmailInclusionList
from ..forms import CustomUserCreationForm


class FormRequestRegister(TypedDict):
    first_name: str
    last_name: str
    email: str
    email_confirm: str
    password1: str
    password2: str


class CustomUserCreationFormTestCase(TestCase):
    """
    Form tests for registering users

    Methods
    -------
    setUp()
        Sets up the test environment

    test_form_conforms()
        Tests if form.is_valid() is working as expected

    test_form_email_not_in_inclusion_list()
        Returns an error with email not in inclusion list

    test_form_email_already_registered_error()
        Returns an error if email is already registered

    test_form_emails_do_not_match()
        Returns an error if emails do not match
    """

    def setUp(self):
        """ Sets up the test environment with a request factory """
        self.factory: RequestFactory = RequestFactory()

    def test_form_conforms(self):
        """ Tests if form.is_valid() is working as expected """
        request: HttpRequest = self.factory.get(reverse("users:register"))
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        data: FormRequestRegister = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin2@email.com",
            "password1": "12345",
            "password2": "12345",
        }

        form: CustomUserCreationForm = CustomUserCreationForm(
            data=data or None, request=request
        )

        self.assertTrue(form.is_valid())

    def test_form_email_not_in_inclusion_list(self):
        """ Returns an error with email not in inclusion list """
        request: HttpRequest = self.factory.get(reverse("users:register"))

        data: FormRequestRegister = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin3@email.com",
            "password1": "12345",
            "password2": "12345",
        }

        form: CustomUserCreationForm = CustomUserCreationForm(
            data=data or None, request=request
        )

        self.assertEqual(
            form.errors["email_confirm"], ["This email is not permitted to sign up"]
        )

    def test_form_email_already_registered_error(self):
        """ Returns an error if email is already registered """
        request: HttpRequest = self.factory.get(reverse("users:register"))
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        User.objects.create(username="admin2@email.com", email="admin2@email.com")
        data: FormRequestRegister = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin2@email.com",
            "password1": "12345",
            "password2": "12345",
        }

        form: CustomUserCreationForm = CustomUserCreationForm(
            data=data or None, request=request
        )

        self.assertEqual(
            form.errors["email_confirm"], ["This email is already registered"]
        )

    def test_form_emails_do_not_match(self):
        """ Returns an error if emails do not match """
        request: HttpRequest = self.factory.get(reverse("users:register"))
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        data: FormRequestRegister = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin3@email.com",
            "password1": "12345",
            "password2": "12345",
        }

        form: CustomUserCreationForm = CustomUserCreationForm(
            data=data or None, request=request
        )

        self.assertEqual(
            form.errors["email_confirm"], ["The email fields do not match"]
        )
