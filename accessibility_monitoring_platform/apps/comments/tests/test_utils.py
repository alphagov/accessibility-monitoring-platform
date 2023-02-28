""" Tests - test for comments model """
import pytest
from datetime import datetime

from django.contrib.auth.models import User
from django.http import HttpRequest
from django.urls import reverse

from ...cases.models import Case
from ...notifications.models import Notification

from ..models import Comment
from ..utils import add_comment_notification

COMMENT_BODY: str = "Comment body"


@pytest.mark.django_db
def test_add_comment_notification(rf):
    """Test add comment notifications"""
    case: Case = Case.objects.create()

    first_user: User = User.objects.create(
        username="first", first_name="First", last_name="User"
    )
    first_request: HttpRequest = rf.get("/")
    first_request.user = first_user

    comment: Comment = Comment.objects.create(
        case=case,
        user=first_user,
        body=COMMENT_BODY,
    )

    assert add_comment_notification(request=first_request, comment=comment)
    assert Notification.objects.count() == 0

    second_user: User = User.objects.create(
        username="second", first_name="Second", last_name="User"
    )
    second_request: HttpRequest = rf.get("/")
    second_request.user = second_user

    second_comment: Comment = Comment.objects.create(
        case=case,
        user=second_user,
        body="this is a comment by a second user",
    )

    assert add_comment_notification(request=second_request, comment=second_comment)
    assert Notification.objects.count() == 1

    notification: Notification = Notification.objects.all().first()
    assert (
        str(notification)
        == "Notification Second User left a message in discussion:\n\nthis is a comment by a second user for first"
    )
