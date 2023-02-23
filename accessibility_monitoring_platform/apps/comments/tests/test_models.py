""" Tests - test for comments model """
import pytest
from datetime import datetime

from django.contrib.auth.models import User

from ..models import Comment, CommentHistory

USER_PASSWORD = "12345"


def create_user() -> User:
    """Creates a user and auto increments the email/username

    Returns:
        User: A user model
    """
    num: int = User.objects.count()
    user: User = User.objects.create(
        username=f"user{num}@email.com", email=f"user{num}@email.com"
    )
    user.set_password(USER_PASSWORD)
    user.save()
    return user


@pytest.mark.django_db
def test_comment_model_returns_str():
    """Comment returns correct string"""
    user: User = create_user()
    comment: Comment = Comment(
        user=user,
        body="this is a comment",
        created_date=datetime.now(),
    )
    assert str(comment) == f"Comment this is a comment by {user.email}"


@pytest.mark.django_db
def test_comment_history_model_returns_str():
    """CommentHistory returns correct string"""
    user: User = create_user()
    comment: Comment = Comment(
        user=user,
        body="this is a comment",
        created_date=datetime.now(),
    )
    comment_history: CommentHistory = CommentHistory(
        comment=comment,
        before="this is a comment",
        after="this is a new comment",
        created_date=datetime.now(),
    )
    assert (
        str(comment_history)
        == "Comment this is a comment was updated to this is a new comment"
    )
