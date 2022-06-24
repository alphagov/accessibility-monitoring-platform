"""
Tests for view - users
"""
from typing import Dict, TypedDict, List

from django.test import TestCase
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from ...common.models import Platform
from ...common.utils import get_platform_settings
from ...notifications.models import NotificationSetting

from ..models import EmailInclusionList


class FormRequestRegister(TypedDict):
    first_name: str
    last_name: str
    email: str
    email_confirm: str
    password1: str
    password2: str


class UserRegisterViewTests(TestCase):
    """
    View tests for users

    Methods
    -------
    setUp()
        Sets up the test environment

    test_register_loads_correctly_no_auth()
        Tests register without authentication

    test_register_redirects_with_auth()
        Tests register reidrects with authentication

    test_register_post_redirects()
        Tests whether if register redirects after registering

    test_register_post_saves_correctly()
        Tests if register saves to the database correctly

    test_register_post_errors_appear()
        Tests whether errors appear if there is a mistake in the form

    """

    def setUp(self):
        """Creates a user for testing the views"""
        user: User = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()

    def test_register_loads_correctly_no_auth(self):
        """Tests if register page loads correctly"""
        response: HttpResponse = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fill in the form below to create an account")

    def test_register_redirects_with_auth(self):
        """Tests if register redirects when logged in"""
        self.client.login(username="testuser", password="12345")
        response: HttpResponse = self.client.get(
            path=reverse("users:register"), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, """<h1 class="govuk-heading-xl">Your cases</h1>""", html=True)

    def test_register_post_redirects(self):
        """Tests if register redirects to dashboard after post request"""
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        data: FormRequestRegister = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin2@email.com",
            "password1": "12345",
            "password2": "12345",
        }
        response: HttpResponse = self.client.post(
            reverse("users:register"), data=data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your cases")

    def test_register_post_saves_correctly(self):
        """Tests if register saves to the database correctly"""
        EmailInclusionList.objects.create(inclusion_email="admin2@email.com")
        data: FormRequestRegister = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin2@email.com",
            "password1": "12345",
            "password2": "12345",
        }
        response: HttpResponse = self.client.post(
            reverse("users:register"), data=data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        user: User = get_object_or_404(User, email="admin2@email.com")
        self.assertEqual(user.first_name, "Joe")
        self.assertEqual(user.last_name, "Blogs")
        self.assertEqual(user.email, "admin2@email.com")
        self.assertEqual(user.username, "admin2@email.com")

    def test_register_post_errors_appear(self):
        """Tests if error message appears if there is a mistake in the form"""
        data: FormRequestRegister = {
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin3@email.com",
            "email_confirm": "admin3@email.com",
            "password1": "12345",
            "password2": "12345",
        }
        response: HttpResponse = self.client.post(
            reverse("users:register"), data=data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This email is not permitted to sign up")


class UserViewTests(TestCase):
    """
    View tests for users

    Methods
    -------
    setUp()
        Sets up the test environment

    test_account_details_loads_correctly_with_auth()
        Tests account details with authentication

    test_account_details_loads_correctly_no_auth()
        Tests account details with no authentication

    test_account_details_post_saves_correctly
        Tests if the form saves correctly and shows the success message

    test_account_details_post_errors_appear
        Tests whether errors appear if there is a mistake in the form
    """

    def setUp(self):
        """Creates a user for testing the views"""
        user: User = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        NotificationSetting(user=user).save()
        self.user = user

    def test_account_details_loads_correctly_with_auth(self):
        """Tests if a user is logged in and can access account details"""
        self.client.login(username="testuser", password="12345")
        response: HttpResponse = self.client.get(reverse("users:account_details", kwargs={"pk": self.user.id}))
        self.assertEqual(str(response.context["user"]), "testuser")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account details")

    # def test_account_details_loads_correctly_no_auth(self):
    #     """Tests if a unauthenticated user returns a 302 response"""
    #     import pdb; pdb.set_trace()
    #     response: HttpResponse = self.client.get(reverse("users:account_details", kwargs={"pk": self.user.id}))
    #     self.assertEqual(response.status_code, 302)

    def test_account_details_post_saves_correctly(self):
        """Tests if form saves correctly and show success message"""
        EmailInclusionList.objects.create(inclusion_email="admin@email.com")
        user: User = User.objects.create(username="joe_blogs", email="admin@email.com")
        user.set_password("12345")
        user.save()
        qa_auditor_group: Group = Group.objects.create(name="QA auditor")
        user.groups.add(qa_auditor_group)
        self.client.login(username="joe_blogs", password="12345")

        data: Dict[str, str] = {
            "email_notifications_enabled": "yes",
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin@email.com",
            "email_confirm": "admin@email.com",
            "password": "12345",
        }

        response: HttpResponse = self.client.post(
            reverse("users:account_details", kwargs={"pk": user.id}),
            data=data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account details")
        messages: List[str] = [str(x) for x in list(response.context["messages"])]
        self.assertEqual(messages[0], "Successfully saved details!")
        platform: Platform = get_platform_settings()

    def test_account_details_post_errors_appear(self):
        """Tests if error message appears if there is a mistake in the form"""
        user: User = User.objects.create(username="joe_blogs", email="admin@email.com")
        user.set_password("12345")
        user.save()
        NotificationSetting(user=user).save()
        self.client.login(username="joe_blogs", password="12345")

        data: Dict[str, str] = {
            "email_notifications_enabled": "yes",
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin@email.com",
            "email_confirm": "admin@email.com",
            "password": "123456",
        }

        response: HttpResponse = self.client.post(
            reverse("users:account_details", kwargs={"pk": user.id}),
            data=data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password is incorrect")
