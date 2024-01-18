""" Tests - test for notifications template tags """
from typing import Optional

import pytest
from django.contrib.auth.models import User
from django.http import HttpRequest

from ..models import Notification, NotificationSetting
from ..utils import (
    add_notification,
    get_number_of_unread_notifications,
    read_notification,
)


@pytest.mark.django_db
def test_read_notifications_marks_notification_as_read(rf):
    """test to check if read_notifications function marks notifications as read"""
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user

    notification: Notification = Notification.objects.create(
        user=user, path=request.path
    )

    assert not notification.read

    read_notification(request)

    notification_from_db: Notification = Notification.objects.get(id=notification.id)  # type: ignore

    assert notification_from_db.read


@pytest.mark.django_db
def test_add_notification_creates_notification_and_sends_email(mailoutbox, rf):
    """test to check if add_notification adds notification and sends email"""
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user
    NotificationSetting.objects.create(user=user)

    assert Notification.objects.all().first() is None

    add_notification(
        user=user,
        body="this is a notification",
        path="/",
        list_description="There is a notification",
        request=request,
    )

    notification: Optional[Notification] = Notification.objects.all().first()

    assert notification is not None
    assert notification.body == "this is a notification"

    assert len(mailoutbox) == 1
    assert (
        mailoutbox[0].subject
        == "You have a new notification in the monitoring platform : There is a notification"
    )


@pytest.mark.django_db
def test_add_notification_creates_notification_and_sends_no_email(mailoutbox, rf):
    """test to check if add_notification adds notification and doesn't send email"""
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user
    NotificationSetting.objects.create(user=user, email_notifications_enabled=False)

    assert Notification.objects.all().first() is None

    add_notification(
        user=user,
        body="this is a notification",
        path="/",
        list_description="There is a notification",
        request=request,
    )

    notification: Optional[Notification] = Notification.objects.all().first()

    assert notification is not None
    assert notification.body == "this is a notification"

    assert len(mailoutbox) == 0


@pytest.mark.django_db
def test_creates_new_email_notification_model_when_null(mailoutbox, rf):
    """
    Test to see if add_notification will create a NotificationSetting
    model when none exists
    """
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user

    assert Notification.objects.all().first() is None
    assert NotificationSetting.objects.all().first() is None

    add_notification(
        user=user,
        body="this is a notification",
        path="/",
        list_description="There is a notification",
        request=request,
    )

    notification: Optional[Notification] = Notification.objects.all().first()

    assert notification is not None
    assert notification.body == "this is a notification"

    assert len(mailoutbox) == 0

    notification_setting: Optional[
        NotificationSetting
    ] = NotificationSetting.objects.all().first()

    assert notification_setting is not None
    assert notification_setting.user.email == user.email
    assert notification_setting.email_notifications_enabled is False


@pytest.mark.django_db
def test_get_number_of_unread_notifications():
    """Check that the number of unread notifications is returned"""
    user: User = User.objects.create()

    notification: Notification = Notification.objects.create(user=user)

    assert get_number_of_unread_notifications(user=user) == 1

    notification.read = True
    notification.save()

    assert get_number_of_unread_notifications(user=user) == 0
