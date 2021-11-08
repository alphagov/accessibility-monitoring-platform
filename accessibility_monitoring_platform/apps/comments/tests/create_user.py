"""Tests - function to generate user"""

from django.contrib.auth.models import User

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
