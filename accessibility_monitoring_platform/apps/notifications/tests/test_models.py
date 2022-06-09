""" Tests - test for notifications models """
import pytest
from datetime import datetime
from django.contrib.auth.models import User
from ..models import Notification, NotificationSetting
from .create_user import create_user


@pytest.mark.django_db
def test_notifications_model_returns_str():
    """Notifications returns correct string"""
    user0: User = create_user()
    notifications: Notification = Notification(
        user=user0,
        body="this is a notification",
        created_date=datetime.now(),
    )
    assert (
        str(notifications) == "Notification this is a notification for user0@email.com"
    )


@pytest.mark.django_db
def test_notifications_settings_returns_str():
    """NotificationsSettings returns correct string"""
    user0: User = create_user()
    notifications = NotificationSetting(user=user0, email_notifications_enabled=True)
    assert str(notifications) == "user0@email.com - email_notifications_enabled is True"
