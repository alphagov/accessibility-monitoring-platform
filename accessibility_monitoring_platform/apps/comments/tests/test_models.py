""" Tests - test for comments model """
import pytest
from datetime import datetime

from django.contrib.auth.models import User

from ..models import Comments, CommentsHistory
from .create_user import create_user


@pytest.mark.django_db
def test_comments_model_returns_str():
    """Comments returns correct string"""
    user: User = create_user()
    comment: Comments = Comments(
        user=user,
        page="page",
        body="this is a comment",
        created_date=datetime.now(),
    )
    assert str(comment) == f"Comment this is a comment by {user.email}"


@pytest.mark.django_db
def test_comments_history_model_returns_str():
    """CommentsHistory returns correct string"""
    user: User = create_user()
    comment: Comments = Comments(
        user=user,
        page="page",
        body="this is a comment",
        created_date=datetime.now(),
    )
    comment_history: CommentsHistory = CommentsHistory(
        comment=comment,
        before="this is a comment",
        after="this is a new comment",
        created_date=datetime.now(),
    )
    assert (
        str(comment_history)
        == "Comment this is a comment was updated to this is a new comment"
    )
