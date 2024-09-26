""" Tests - test for notifications models """

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from ...cases.models import Case
from ...common.models import Link
from ..models import NotificationSetting, Task


@pytest.mark.django_db
def test_notifications_settings_returns_str():
    """NotificationSetting object returns correct string"""
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )

    notification_setting = NotificationSetting(user=user)

    assert str(notification_setting) == f"{user} - email_notifications_enabled is True"


@pytest.mark.django_db
def test_options_qa_comment():
    """Task options for QA comment"""
    user: User = User.objects.create()
    case: Case = Case.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.QA_COMMENT,
        date=date.today(),
        case=case,
        user=user,
    )

    assert task.options() == [
        Link(
            label="Go to QA comment",
            url=reverse(
                "cases:edit-qa-comments",
                kwargs={"pk": case.id},
            ),
        ),
        Link(
            label="Mark as seen",
            url=reverse(
                "notifications:mark-task-read",
                kwargs={"pk": task.id},
            ),
        ),
        Link(
            label="Mark case tasks as seen",
            url=reverse(
                "notifications:mark-case-comments-read",
                kwargs={"case_id": case.id},
            ),
        ),
    ]


@pytest.mark.django_db
def test_options_report_approved():
    """Task options for report approved"""
    user: User = User.objects.create()
    case: Case = Case.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.REPORT_APPROVED,
        date=date.today(),
        case=case,
        user=user,
    )

    assert task.options() == [
        Link(
            label="Go to Report approved",
            url=reverse(
                "cases:edit-report-approved",
                kwargs={"pk": case.id},
            ),
        ),
        Link(
            label="Mark as seen",
            url=reverse(
                "notifications:mark-task-read",
                kwargs={"pk": task.id},
            ),
        ),
        Link(
            label="Mark case tasks as seen",
            url=reverse(
                "notifications:mark-case-comments-read",
                kwargs={"case_id": case.id},
            ),
        ),
    ]


@pytest.mark.django_db
def test_options_reminder():
    """Task options for reminder"""
    user: User = User.objects.create()
    case: Case = Case.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        case=case,
        user=user,
    )

    assert task.options() == [
        Link(
            label="Edit",
            url=reverse(
                "notifications:edit-reminder-task",
                kwargs={"pk": task.id},
            ),
        ),
        Link(
            label="Delete reminder",
            url=reverse(
                "notifications:mark-task-read",
                kwargs={"pk": task.id},
            ),
        ),
    ]
