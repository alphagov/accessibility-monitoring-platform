""" Tests - test for notifications view """
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from ..models import Notification

UNREAD_NOTIFICATION_BODY: str = "Unread notification"
READ_NOTIFICATION_BODY: str = "Read notification"


def test_list_notifications_defaults_to_showing_unread(admin_client, admin_user):
    """Test list of notifications defaults to showing unread"""
    Notification.objects.create(user=admin_user, body=UNREAD_NOTIFICATION_BODY)
    Notification.objects.create(user=admin_user, body=READ_NOTIFICATION_BODY, read=True)

    response: HttpResponse = admin_client.get(
        f'{reverse("notifications:notifications-list")}'
    )

    assertContains(response, UNREAD_NOTIFICATION_BODY)
    assertNotContains(response, READ_NOTIFICATION_BODY)


def test_list_notifications_shows_unread_on_demand(admin_client, admin_user):
    """Test list of notifications shows unread on demand"""
    Notification.objects.create(user=admin_user, body=UNREAD_NOTIFICATION_BODY)
    Notification.objects.create(user=admin_user, body=READ_NOTIFICATION_BODY, read=True)

    response: HttpResponse = admin_client.get(
        f'{reverse("notifications:notifications-list")}?showing=unread'
    )

    assertContains(response, UNREAD_NOTIFICATION_BODY)
    assertNotContains(response, READ_NOTIFICATION_BODY)


def test_list_notifications_shows_all_on_demand(admin_client, admin_user):
    """Test list of notifications shows all on demand"""
    Notification.objects.create(user=admin_user, body=UNREAD_NOTIFICATION_BODY)
    Notification.objects.create(user=admin_user, body=READ_NOTIFICATION_BODY, read=True)

    response: HttpResponse = admin_client.get(
        f'{reverse("notifications:notifications-list")}?showing=all'
    )

    assertContains(response, UNREAD_NOTIFICATION_BODY)
    assertContains(response, READ_NOTIFICATION_BODY)


def test_mark_notification_as_read(admin_client, admin_user):
    """Test marking notification as read"""
    notification: Notification = Notification.objects.create(
        user=admin_user, body=READ_NOTIFICATION_BODY
    )

    response: HttpResponse = admin_client.get(
        reverse("notifications:mark-notification-read", kwargs={"pk": notification.id}),  # type: ignore
        follow=True,
    )

    assert response.status_code == 200
    assertContains(response, "Notification marked as seen")

    notification_from_db: Notification = Notification.objects.get(id=notification.id)  # type: ignore

    assert notification_from_db.read


def test_mark_notification_as_unread(admin_client, admin_user):
    """Test marking notification as unread"""
    notification: Notification = Notification.objects.create(
        user=admin_user, body=READ_NOTIFICATION_BODY, read=True
    )

    response: HttpResponse = admin_client.get(
        reverse(
            "notifications:mark-notification-unread", kwargs={"pk": notification.id}  # type: ignore
        ),
        follow=True,
    )

    assert response.status_code == 200
    assertContains(response, "Notification marked as unseen")

    notification_from_db: Notification = Notification.objects.get(id=notification.id)  # type: ignore

    assert not notification_from_db.read
