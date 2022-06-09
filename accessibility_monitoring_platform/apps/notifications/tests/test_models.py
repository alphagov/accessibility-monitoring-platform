""" Tests - test for notifications models """
import pytest

from django.contrib.auth.models import User

from ..models import Notification, NotificationSetting


@pytest.mark.django_db
def test_notifications_model_returns_str():
    """Notifications returns correct string"""
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    notification: Notification = Notification(
        user=user,
        body="this is a notification",
    )
    assert (
        str(notification) == f"Notification this is a notification for {user}"
    )


@pytest.mark.django_db
def test_notifications_settings_returns_str():
    """NotificationSetting object returns correct string"""
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )

    notification_setting = NotificationSetting(user=user)

    assert str(notification_setting) == f"{user} - email_notifications_enabled is True"
