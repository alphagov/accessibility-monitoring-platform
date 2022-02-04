""" Tests - test for notifications template tags """
import pytest
from datetime import datetime
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.core.handlers.wsgi import WSGIRequest
from ..models import Notifications, NotificationsSettings
from ..utils import read_notification, add_notification
from .create_user import create_user


@pytest.mark.django_db
def test_read_notifications_marks_notification_as_read():
    """test to check if read_notifications function marks notifications as read"""
    user0: User = create_user()
    notification: Notifications = Notifications(
        user=user0, body="this is a notification", created_date=datetime.now(), path="/"
    )
    notification.save()
    factory: RequestFactory = RequestFactory()
    request: WSGIRequest = factory.get("/")
    request.user = user0

    read_notification(request)
    assert Notifications.objects.get(id=notification.id).read is True  # type: ignore


@pytest.mark.django_db
def test_add_notification_creates_notification_and_sends_email(mailoutbox):
    """test to check if add_notification adds notification and sends email"""
    user0: User = create_user()
    NotificationsSettings(user=user0).save()
    factory = RequestFactory()
    request: WSGIRequest = factory.get("/")
    request.user = user0
    add_notification(
        user=user0,
        body="this is a notification",
        path="/",
        list_description="There is a notification",
        request=request,
    )
    assert Notifications.objects.get(id=1).body == "this is a notification"
    assert len(mailoutbox) == 1
    assert (
        mailoutbox[0].subject
        == "You have a new notification in the monitoring platform : There is a notification"
    )


@pytest.mark.django_db
def test_add_notification_creates_notification_and_sends_no_email(mailoutbox):
    """test to check if add_notification adds notification and doesn't send email"""
    user0: User = create_user()
    NotificationsSettings(
        user=user0,
        email_notifications_enabled=False,
    ).save()
    factory: RequestFactory = RequestFactory()
    request: WSGIRequest = factory.get("/")
    request.user = user0
    add_notification(
        user=user0,
        body="this is a notification",
        path="/",
        list_description="There is a notification",
        request=request,
    )
    assert Notifications.objects.get(id=1).body == "this is a notification"
    assert len(mailoutbox) == 0


@pytest.mark.django_db
def test_creates_new_email_notification_model_when_null(mailoutbox):
    """test to see if add_notification will create a NotificationsSettings model when none exists"""
    user0: User = create_user()
    assert len(NotificationsSettings.objects.all()) == 0
    factory: RequestFactory = RequestFactory()
    request: WSGIRequest = factory.get("/")
    request.user = user0
    add_notification(
        user=user0,
        body="this is a notification",
        path="/",
        list_description="There is a notification",
        request=request,
    )
    assert Notifications.objects.get(id=1).body == "this is a notification"
    assert len(mailoutbox) == 0
    assert len(NotificationsSettings.objects.all()) == 1
    assert NotificationsSettings.objects.get(user=1).user.email == user0.email
    assert (
        NotificationsSettings.objects.get(user=1).email_notifications_enabled is False
    )
