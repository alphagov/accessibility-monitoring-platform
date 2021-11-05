""" Tests - test for notifications models """
import pytest
from datetime import datetime
from django.contrib.auth.models import User
from ..models import Notifications, NotificationsSettings

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
def test_notifications_model_returns_str():
    """Notifications returns correct string"""
    user0: User = create_user()
    notifications: Notifications = Notifications(
        user=user0,
        body="this is a notification",
        created_date=datetime.now(),
    )
    assert str(notifications) == "Notification this is a notification for user0@email.com"


@pytest.mark.django_db
def test_notifications_settings_returns_str():
    """NotificationsSettings returns correct string"""
    user0: User = create_user()
    notifications = NotificationsSettings(
        user=user0,
        email_notifications_enabled=True
    )
    assert str(notifications) == "user0@email.com - email_notifications_enabled is True"
