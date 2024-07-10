"""Test notifications views"""

from datetime import date, timedelta

import pytest
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from ...cases.models import Case
from ...common.models import Event
from ..models import Task
from ..views import (
    CommentsMarkAsReadView,
    ReminderTaskCreateView,
    ReminderTaskUpdateView,
    TaskListView,
    TaskMarkAsReadView,
)

TODAY: date = date.today()
DESCRIPTION: str = "Task description"


class MockMessages:
    def __init__(self):
        self.messages = []

    def add(self, level: str, message: str, extra_tags: str) -> None:
        self.messages.append((level, message, extra_tags))


@pytest.mark.django_db
def test_empty_task_list(rf):
    """Test empty task list page renders"""
    user: User = User.objects.create()

    request: HttpRequest = rf.get(reverse("notifications:task-list"))
    request.user = user

    response: HttpResponse = TaskListView.as_view()(request)

    assert response.status_code == 200
    assertContains(response, "Tasks (0)")


@pytest.mark.django_db
def test_task_list(rf):
    """Test task list page renders"""
    user: User = User.objects.create()
    case: Case = Case.objects.create(auditor=user)
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        case=case,
    )

    request: HttpRequest = rf.get(reverse("notifications:task-list"))
    request.user = user

    response: HttpResponse = TaskListView.as_view()(request)

    assert response.status_code == 200
    assertContains(response, "Tasks (1)")


@pytest.mark.django_db
def test_task_list_other_user(rf):
    """Test task list page can show other user's tasks"""
    request_user: User = User.objects.create(
        username="mockuser1", email="mockuser1@mock.com", password="secret1"
    )
    other_user: User = User.objects.create(
        username="mockuser2", email="mockuser2@mock.com", password="secret2"
    )
    case: Case = Case.objects.create(auditor=other_user)
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=other_user,
        case=case,
    )

    request: HttpRequest = rf.get(
        f'{reverse("notifications:task-list")}?user_id={other_user.id}'
    )
    request.user = request_user

    response: HttpResponse = TaskListView.as_view()(request)

    assert response.status_code == 200
    assertContains(response, "Tasks (1)")


@pytest.mark.parametrize(
    "filtered_type, other_type",
    [
        ("qa-comment", "reminder"),
        ("report-approved", "reminder"),
        ("reminder", "qa-comment"),
    ],
)
@pytest.mark.django_db
def test_task_list_type_filter(filtered_type, other_type, rf):
    """Test task list type filters"""
    user: User = User.objects.create()
    case: Case = Case.objects.create(auditor=user)
    filtered_task: Task = Task.objects.create(
        type=filtered_type,
        date=date.today(),
        user=user,
        case=case,
    )
    other_task: Task = Task.objects.create(
        type=other_type,
        date=date.today(),
        user=user,
        case=case,
    )

    request: HttpRequest = rf.get(
        f'{reverse("notifications:task-list")}?type={filtered_type}'
    )
    request.user = user

    response: HttpResponse = TaskListView.as_view()(request)

    assert response.status_code == 200

    assertContains(response, "Tasks (1)")
    assertContains(response, f"{filtered_task.get_type_display()}</h2>")
    assertNotContains(response, f"{other_task.get_type_display()}</h2>")


@pytest.mark.parametrize("read_param", ["read", "deleted"])
@pytest.mark.django_db
def test_task_list_read_filter(read_param, rf):
    """Test task list read filter"""
    user: User = User.objects.create()
    case: Case = Case.objects.create(auditor=user)
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        case=case,
        description=DESCRIPTION,
        read=True,
    )
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        case=case,
    )

    request: HttpRequest = rf.get(
        f'{reverse("notifications:task-list")}?{read_param}=true'
    )
    request.user = user

    response: HttpResponse = TaskListView.as_view()(request)

    assert response.status_code == 200

    assertContains(response, "Tasks (1)")
    assertContains(response, DESCRIPTION)


@pytest.mark.django_db
def test_task_list_future_filter(rf):
    """Test task list future filter"""
    user: User = User.objects.create()
    case: Case = Case.objects.create(auditor=user)
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today() + timedelta(days=7),
        user=user,
        case=case,
        description=DESCRIPTION,
    )
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        case=case,
    )

    request: HttpRequest = rf.get(f'{reverse("notifications:task-list")}?future=true')
    request.user = user

    response: HttpResponse = TaskListView.as_view()(request)

    assert response.status_code == 200

    assertContains(response, "Tasks (1)")
    assertContains(response, DESCRIPTION)


@pytest.mark.django_db
def test_reminder_task_create_redirects_to_case(rf):
    """
    Test creating a reminder task redirects to parent case details
    """
    user: User = User.objects.create()
    case: Case = Case.objects.create(auditor=user)

    request: HttpRequest = rf.post(
        reverse("notifications:reminder-create", kwargs={"case_id": case.id}),
        {
            "date_0": TODAY.day,
            "date_1": TODAY.month,
            "date_2": TODAY.year,
            "description": DESCRIPTION,
            "save": "Save",
        },
    )
    request.user = user

    response: HttpResponse = ReminderTaskCreateView.as_view()(request, case_id=case.id)

    assert response.status_code == 302
    assert response.url == reverse("cases:case-detail", kwargs={"pk": case.id})

    task: Task = Task.objects.all().first()

    assert task is not None
    assert task.type == Task.Type.REMINDER
    assert task.date == TODAY
    assert task.description == DESCRIPTION

    event: Event = Event.objects.all().first()

    assert event is not None
    assert event.type == Event.Type.CREATE


@pytest.mark.django_db
def test_reminder_task_update_redirects_to_case(rf):
    """
    Test updating a reminder task redirects to parent case details
    """
    user: User = User.objects.create()
    case: Case = Case.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        case=case,
    )

    request: HttpRequest = rf.post(
        reverse("notifications:edit-reminder-task", kwargs={"pk": task.id}),
        {
            "date_0": TODAY.day,
            "date_1": TODAY.month,
            "date_2": TODAY.year,
            "description": DESCRIPTION,
            "save": "Save",
        },
    )
    request.user = user

    response: HttpResponse = ReminderTaskUpdateView.as_view()(request, pk=task.id)

    assert response.status_code == 302
    assert response.url == reverse("cases:case-detail", kwargs={"pk": case.id})

    task_from_db: Task = Task.objects.get(id=task.id)

    assert task_from_db is not None
    assert task_from_db.description == DESCRIPTION

    event: Event = Event.objects.all().first()

    assert event is not None
    assert event.type == Event.Type.UPDATE


@pytest.mark.django_db
def test_task_mark_as_read(rf):
    """Test marking task as read"""
    user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    case: Case = Case.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.QA_COMMENT,
        date=date.today(),
        user=user,
        case=case,
    )

    request = rf.get(reverse("notifications:mark-task-read", kwargs={"pk": task.id}))
    request.user = user
    request._messages = MockMessages()

    assert task.read is False

    response: HttpResponse = TaskMarkAsReadView.as_view()(request, pk=task.id)

    assert response.status_code == 302
    assert response.url == reverse("notifications:task-list")
    assert len(request._messages.messages) == 1
    assert (
        request._messages.messages[0][1]
        == f"{task.case} {task.get_type_display()} task marked as read"
    )

    task_from_db: Task = Task.objects.get(id=task.id)

    assert task_from_db.read is True


@pytest.mark.django_db
def test_comments_mark_as_read_marks_tasks_as_read(rf):
    """
    Test marking case comments as read marks QA comment and Report
    approved tasks as read.
    """
    user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    case: Case = Case.objects.create(auditor=user)
    qa_comment_task: Task = Task.objects.create(
        type=Task.Type.QA_COMMENT,
        date=date.today(),
        user=user,
        case=case,
    )
    report_approved_task: Task = Task.objects.create(
        type=Task.Type.REPORT_APPROVED,
        date=date.today(),
        user=user,
        case=case,
    )

    request = rf.get(
        reverse("notifications:mark-case-comments-read", kwargs={"case_id": case.id})
    )
    request.user = user
    request._messages = MockMessages()

    assert qa_comment_task.read is False
    assert report_approved_task.read is False

    response: HttpResponse = CommentsMarkAsReadView.as_view()(request, case_id=case.id)

    assert response.status_code == 302
    assert response.url == reverse("notifications:task-list")
    assert len(request._messages.messages) == 1
    assert request._messages.messages[0][1] == f"{case} comments marked as read"

    qa_comment_task_from_db: Task = Task.objects.get(id=qa_comment_task.id)

    assert qa_comment_task_from_db.read is True

    report_approved_task_from_db: Task = Task.objects.get(id=report_approved_task.id)

    assert report_approved_task_from_db.read is True
