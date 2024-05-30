""" Tests - test for notifications template tags """

from datetime import date
from typing import Optional

import pytest
from django.contrib.auth.models import User
from django.http import HttpRequest

from ...cases.models import Case
from ..models import Notification, NotificationSetting, Task
from ..utils import add_task, get_number_of_unread_notifications, read_tasks


@pytest.mark.django_db
def test_read_tasks_marks_task_as_read(rf):
    """test to check if read_tasks function marks tasks as read"""
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user
    case: Case = Case.objects.create()

    task: Task = Task.objects.create(
        date=date.today(), user=user, case=case, type=Task.Type.QA_COMMENT
    )

    assert not task.read

    read_tasks(user=user, case=case, type=Task.Type.QA_COMMENT)

    task_from_db: Task = Task.objects.get(id=task.id)  # type: ignore

    assert task_from_db.read


@pytest.mark.django_db
@pytest.mark.parametrize(
    "type",
    [Task.Type.QA_COMMENT, Task.Type.REPORT_APPROVED],
)
def test_add_task_creates_task_and_sends_email(type, mailoutbox, rf):
    """test to check if add_task adds task and sends email"""
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user
    NotificationSetting.objects.create(user=user)
    case: Case = Case.objects.create()

    assert Task.objects.all().first() is None

    add_task(
        user=user,
        case=case,
        type=type,
        description="this is a notification",
        list_description="There is a notification",
        request=request,
    )

    task: Optional[Task] = Task.objects.all().first()

    assert task is not None
    assert task.description == "this is a notification"

    assert len(mailoutbox) == 1
    assert (
        mailoutbox[0].subject
        == "You have a new notification in the monitoring platform : There is a notification"
    )


@pytest.mark.django_db
def test_add_task_creates_task_and_sends_no_email(mailoutbox, rf):
    """test to check if add_task adds task and doesn't send email"""
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user
    NotificationSetting.objects.create(user=user, email_notifications_enabled=False)
    case: Case = Case.objects.create()

    assert Task.objects.all().first() is None

    add_task(
        user=user,
        case=case,
        type=type,
        description="this is a notification",
        list_description="There is a notification",
        request=request,
    )

    task: Optional[Task] = Task.objects.all().first()

    assert task is not None
    assert task.description == "this is a notification"

    assert len(mailoutbox) == 0


@pytest.mark.django_db
def test_add_task_creates_new_email_notification_model_when_null(mailoutbox, rf):
    """
    Test to see if add_task will create a NotificationSetting
    model when none exists
    """
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user
    case: Case = Case.objects.create()

    assert Notification.objects.all().first() is None
    assert NotificationSetting.objects.all().first() is None

    add_task(
        user=user,
        case=case,
        type=type,
        description="this is a notification",
        list_description="There is a notification",
        request=request,
    )

    task: Optional[Task] = Task.objects.all().first()

    assert task is not None
    assert task.description == "this is a notification"
    assert len(mailoutbox) == 0

    notification_setting: Optional[NotificationSetting] = (
        NotificationSetting.objects.all().first()
    )

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
