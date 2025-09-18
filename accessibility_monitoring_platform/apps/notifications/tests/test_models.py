"""Tests - test for notifications models"""

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from ...common.models import Link
from ...detailed.models import DetailedCase
from ...simplified.models import SimplifiedCase
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
def test_options_qa_comment_simplified():
    """Task options for QA comment in simplified case"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.QA_COMMENT,
        date=date.today(),
        base_case=simplified_case,
        user=user,
    )

    assert task.options() == [
        Link(
            label="Go to QA comment",
            url=reverse(
                "simplified:edit-qa-comments",
                kwargs={"pk": simplified_case.id},
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
                kwargs={"case_id": simplified_case.id},
            ),
        ),
    ]


@pytest.mark.django_db
def test_options_qa_comment_detailed():
    """Task options for QA comment in detailed case"""
    user: User = User.objects.create()
    detailed_case: DetailedCase = DetailedCase.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.QA_COMMENT,
        date=date.today(),
        base_case=detailed_case,
        user=user,
    )

    assert task.options() == [
        Link(
            label="Go to QA comment",
            url=reverse(
                "detailed:edit-qa-comments",
                kwargs={"pk": detailed_case.id},
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
                kwargs={"case_id": detailed_case.id},
            ),
        ),
    ]


@pytest.mark.django_db
def test_options_report_approved_simplified():
    """Task options for report approved on simplified case"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.REPORT_APPROVED,
        date=date.today(),
        base_case=simplified_case,
        user=user,
    )

    assert task.options() == [
        Link(
            label="Go to Report approved",
            url=reverse(
                "simplified:edit-qa-approval",
                kwargs={"pk": simplified_case.id},
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
                kwargs={"case_id": simplified_case.id},
            ),
        ),
    ]


@pytest.mark.django_db
def test_options_report_approved_detailed():
    """Task options for report approved on detailed case"""
    user: User = User.objects.create()
    detailed_case: DetailedCase = DetailedCase.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.REPORT_APPROVED,
        date=date.today(),
        base_case=detailed_case,
        user=user,
    )

    assert task.options() == [
        Link(
            label="Go to Report approved",
            url=reverse(
                "detailed:edit-qa-approval",
                kwargs={"pk": detailed_case.id},
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
                kwargs={"case_id": detailed_case.id},
            ),
        ),
    ]


@pytest.mark.django_db
def test_options_reminder():
    """Task options for reminder"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        base_case=simplified_case,
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


@pytest.mark.django_db
def test_options_read_reminder():
    """Task options for read reminder"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        base_case=simplified_case,
        user=user,
        read=True,
    )

    assert task.options() == [
        Link(
            label="Create new",
            url=reverse(
                "notifications:reminder-create",
                kwargs={"case_id": simplified_case.id},
            ),
        ),
    ]
