"""
Tests for users forms
"""

from typing import Dict, Optional, TypedDict

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory

from ..forms import UserCreateForm, UserUpdateForm
from ..models import EmailInclusionList


class FormRequestAccountDetails(TypedDict):
    first_name: str
    last_name: str
    email: str
    email_confirm: str
    password: str
    active_qa_auditor: Optional[int]


class FormRequestRegister(TypedDict):
    first_name: str
    last_name: str
    email: str
    email_confirm: str
    password1: str
    password2: str


class UserCreateFormTestCase(TestCase):
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
        """Sets up the test environment with a request factory"""
        self.factory: RequestFactory = RequestFactory()

    def test_form_conforms(self):
        """Tests if form.is_valid() is working as expected"""
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        data: FormRequestRegister = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin2@email.com",
            "password1": "12345",
            "password2": "12345",
        }

        form: UserCreateForm = UserCreateForm(data=data)

        self.assertTrue(form.is_valid())

    def test_form_email_not_in_inclusion_list(self):
        """Returns an error with email not in inclusion list"""
        data: FormRequestRegister = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin3@email.com",
            "email_confirm": "admin3@email.com",
            "password1": "12345",
            "password2": "12345",
        }

        form: UserCreateForm = UserCreateForm(data=data)

        self.assertEqual(
            form.errors["email_confirm"], ["This email is not permitted to sign up"]
        )

    def test_form_email_already_registered_error(self):
        """Returns an error if email is already registered"""
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

        form: UserCreateForm = UserCreateForm(data=data)

        self.assertEqual(
            form.errors["email_confirm"], ["This email is already registered"]
        )

    def test_form_emails_do_not_match(self):
        """Returns an error if emails do not match"""
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        data: FormRequestRegister = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin3@email.com",
            "password1": "12345",
            "password2": "12345",
        }

        form: UserCreateForm = UserCreateForm(data=data)

        self.assertEqual(
            form.errors["email_confirm"], ["The email fields do not match"]
        )


class UserUpdateFormTestCase(TestCase):
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

        data: Dict[str, str] = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "password": "12345",
        }

        form: UserUpdateForm = UserUpdateForm(
            data=data or None,
            user=user,
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

        data: Dict[str, str] = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin2@email.com",
            "password": "WRONG_PASSWORD",
        }

        form: UserUpdateForm = UserUpdateForm(
            data=data or None,
            user=user,
            initial={},
        )

        self.assertEqual(form.errors["password"], ["Password is incorrect"])
