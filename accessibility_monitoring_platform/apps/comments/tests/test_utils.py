"""Tests - test for comments model"""

import pytest
from django.contrib.auth.models import Group, User
from django.http import HttpRequest

from ...common.models import QA_AUDITOR_GROUP_NAME, Platform
from ...common.utils import get_platform_settings
from ...detailed.models import DetailedCase
from ...mobile.models import MobileCase
from ...notifications.models import Task
from ...simplified.models import SimplifiedCase, SimplifiedEventHistory
from ..models import Comment
from ..utils import add_comment_notification

COMMENT_BODY: str = "Comment body"


@pytest.mark.django_db
def test_add_comment_notification(rf):
    """Test add comment notification task"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    first_user: User = User.objects.create(
        username="first", first_name="First", last_name="User"
    )
    first_request: HttpRequest = rf.get("/")
    first_request.user = first_user

    comment: Comment = Comment.objects.create(
        base_case=simplified_case,
        user=first_user,
        body=COMMENT_BODY,
    )

    assert add_comment_notification(request=first_request, comment=comment)
    assert Task.objects.count() == 0

    second_user: User = User.objects.create(
        username="second", first_name="Second", last_name="User"
    )
    second_request: HttpRequest = rf.get("/")
    second_request.user = second_user

    second_comment: Comment = Comment.objects.create(
        base_case=simplified_case,
        user=second_user,
        body="this is a comment by a second user",
    )

    assert add_comment_notification(request=second_request, comment=second_comment)
    assert Task.objects.count() == 1

    task: Task = Task.objects.all().first()

    assert (
        task.description
        == "Second User left a message in discussion:\n\nthis is a comment by a second user"
    )

    simplified_event_history: SimplifiedEventHistory = (
        SimplifiedEventHistory.objects.all().first()
    )

    assert simplified_event_history is not None


@pytest.mark.django_db
def test_add_comment_notification_to_on_call_qa(rf):
    """Test comment notifications are also sent to on-call QA auditor"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    first_user: User = User.objects.create(
        username="first", first_name="First", last_name="User"
    )
    request: HttpRequest = rf.get("/")
    request.user = first_user

    platform: Platform = get_platform_settings()
    second_user: User = User.objects.create(
        username="second", first_name="Second", last_name="User"
    )
    platform.active_qa_auditor = second_user
    platform.save()

    comment: Comment = Comment.objects.create(
        base_case=simplified_case,
        user=first_user,
        body=COMMENT_BODY,
    )

    assert add_comment_notification(request=request, comment=comment)
    assert Task.objects.count() == 1

    task: Task = Task.objects.all().first()

    assert task.user == second_user
    assert task.type == Task.Type.QA_COMMENT


@pytest.mark.parametrize("case_class", [DetailedCase, MobileCase, SimplifiedCase])
@pytest.mark.django_db
def test_add_comment_notification_to_all_qa_auditors(case_class, rf):
    """
    Test comment notifications are also sent to all QA auditors when for a detailed
    or mobile case with no auditor set.
    """
    case: DetailedCase | MobileCase | SimplifiedCase = case_class.objects.create()

    requesting_user: User = User.objects.create(
        username="first", first_name="First", last_name="User"
    )
    request: HttpRequest = rf.get("/")
    request.user = requesting_user

    first_qa_auditor: User = User.objects.create(
        username="second", first_name="Second", last_name="User"
    )
    second_qa_auditor: User = User.objects.create(
        username="third", first_name="Third", last_name="User"
    )

    qa_group: Group = Group.objects.create(name=QA_AUDITOR_GROUP_NAME)
    qa_group.user_set.add(requesting_user)
    qa_group.user_set.add(first_qa_auditor)
    qa_group.user_set.add(second_qa_auditor)

    comment: Comment = Comment.objects.create(
        base_case=case,
        user=requesting_user,
        body=COMMENT_BODY,
    )

    assert add_comment_notification(request=request, comment=comment)

    if case_class == SimplifiedCase:
        assert Task.objects.count() == 0
    else:
        assert Task.objects.count() == 2
