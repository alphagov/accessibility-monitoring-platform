"""
Tests for view - users
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import HttpResponse
from ..models import EmailInclusionList
from ...notifications.models import NotificationsSettings
from typing import TypedDict, List


class FormRequestAccountDetails(TypedDict):
    email_notifications_enabled: str
    first_name: str
    last_name: str
    email: str
    email_confirm: str
    password: str


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
        """ Creates a user for testing the views """
        user: User = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        NotificationsSettings(user=user).save()

    def test_account_details_loads_correctly_with_auth(self):
        """ Tests if a user is logged in and can access account details """
        self.client.login(username="testuser", password="12345")
        response: HttpResponse = self.client.get(reverse("users:account_details"))
        self.assertEqual(str(response.context["user"]), "testuser")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account details")

    def test_account_details_loads_correctly_no_auth(self):
        """ Tests if a unauthenticated user returns a 302 response """
        response: HttpResponse = self.client.get(reverse("users:account_details"))
        self.assertEqual(response.status_code, 302)

    def test_account_details_post_saves_correctly(self):
        """ Tests if form saves correctly and show success message """
        EmailInclusionList.objects.create(inclusion_email="admin@email.com")
        user: User = User.objects.create(username="joe_blogs", email="admin@email.com")
        user.set_password("12345")
        user.save()
        NotificationsSettings(user=user).save()
        self.client.login(username="joe_blogs", password="12345")

        data: FormRequestAccountDetails = {
            "email_notifications_enabled": "yes",
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin@email.com",
            "email_confirm": "admin@email.com",
            "password": "12345",
        }

        response: HttpResponse = self.client.post(
            reverse("users:account_details"), data=data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account details")
        messages: List[str] = [str(x) for x in list(response.context["messages"])]
        self.assertEqual(messages[0], "Successfully saved details!")

    def test_account_details_post_errors_appear(self):
        """ Tests if error message appears if there is a mistake in the form """
        user: User = User.objects.create(username="joe_blogs", email="admin@email.com")
        user.set_password("12345")
        user.save()
        NotificationsSettings(user=user).save()
        self.client.login(username="joe_blogs", password="12345")

        data: FormRequestAccountDetails = {
            "email_notifications_enabled": "yes",
            "first_name": "Joe",
            "last_name": "Blogs",
            "email": "admin2@email.com",
            "email_confirm": "admin2@email.com",
            "password": "12345",
        }

        response: HttpResponse = self.client.post(
            reverse("users:account_details"), data=data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This email is not permitted to sign up")
        messages: List[str] = [str(x) for x in list(response.context["messages"])]
        self.assertEqual(messages[0], "There were errors in the form")
