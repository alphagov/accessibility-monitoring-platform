""" Tests - test for notifications view """
import pytest
from pytest_django.asserts import assertContains
from datetime import datetime
from django.contrib.auth.models import User
from django.test import Client
from django.http import HttpResponse
from django.urls import reverse
from ..models import Notifications

USER_PASSWORD = "12345"


def create_user() -> User:
    """Creates a user and auto increments the email/username

    Returns:
        User: A user model
    """
    num: int = len(User.objects.all())
    user: User = User.objects.create(
        username=f"user{num}@email.com",
        email=f"user{num}@email.com"
    )
    user.set_password(USER_PASSWORD)
    user.save()
    return user


@pytest.mark.django_db
def test_view_notifications():
    """Test to see if notifications render in notification centre"""
    user0: User = create_user()
    client: Client = Client()
    client.login(username=user0.username, password=USER_PASSWORD)

    response: HttpResponse = client.get(reverse("notifications:notifications-list"))
    assert response.status_code == 200
    assertContains(response, "Notifications (0)")

    Notifications(
        user=user0,
        body="this is a notification",
        created_date=datetime.now()
    ).save()

    response: HttpResponse = client.get(reverse("notifications:notifications-list"))
    assert response.status_code == 200
    assertContains(response, "Notifications (1)")
    assertContains(response, "this is a notification")


@pytest.mark.django_db
def test_hide_notification():
    """Test to mark notification as seen in notification centre"""
    user0: User = create_user()
    client: Client = Client()
    client.login(username=user0.username, password=USER_PASSWORD)

    notification: Notifications = Notifications(
        user=user0,
        body="this is a notification",
        created_date=datetime.now()
    )
    notification.save()

    response: HttpResponse = client.get(reverse("notifications:notifications-list"))
    assert response.status_code == 200
    assertContains(response, "Notifications (1)")
    assertContains(response, "this is a notification")
    assertContains(response, "Mark as seen")

    response: HttpResponse = client.get(
        reverse(
            "notifications:hide-notification",
            kwargs={"pk": notification.id},  # type: ignore
        ),
        follow=True
    )
    assert response.status_code == 200

    response: HttpResponse = client.get(reverse("notifications:notifications-list"))
    assert response.status_code == 200
    assert Notifications.objects.get(id=notification.id).read is True  # type: ignore
    assertContains(response, "Notifications (0)")
    assertContains(response, "this is a notification")
    assertContains(response, "Mark as unseen")


@pytest.mark.django_db
def test_unhide_notification():
    """Test to unhide notification"""
    user0: User = create_user()
    client: Client = Client()
    client.login(username=user0.username, password=USER_PASSWORD)

    notification: Notifications = Notifications(
        user=user0,
        body="this is a notification",
        created_date=datetime.now()
    )
    notification.save()

    response: HttpResponse = client.get(reverse("notifications:notifications-list"))
    assert response.status_code == 200
    assertContains(response, "Notifications (1)")
    assertContains(response, "this is a notification")
    assertContains(response, "Mark as seen")

    response: HttpResponse = client.get(
        reverse(
            "notifications:hide-notification",
            kwargs={"pk": notification.id},  # type: ignore
        ),
        follow=True
    )
    assert response.status_code == 200

    response: HttpResponse = client.get(reverse("notifications:notifications-list"))
    assert response.status_code == 200
    assert Notifications.objects.get(id=notification.id).read is True  # type: ignore
    assertContains(response, "Notifications (0)")
    assertContains(response, "this is a notification")
    assertContains(response, "Mark as unseen")

    response: HttpResponse = client.get(
        reverse(
            "notifications:unhide-notification",
            kwargs={"pk": notification.id},  # type: ignore
        ),
        follow=True
    )
    assert response.status_code == 200
    assert Notifications.objects.get(id=notification.id).read is False  # type: ignore
    assertContains(response, "Notifications (1)")
    assertContains(response, "this is a notification")
    assertContains(response, "Mark as seen")
