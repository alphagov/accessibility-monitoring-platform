"""Test notifications views"""

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from ...cases.models import Case
from ...common.models import Event
from ..models import Task
from ..views import ReminderTaskCreateView, ReminderTaskUpdateView, TaskListView

TODAY: date = date.today()
DESCRIPTION: str = "Task description"


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


@pytest.mark.parametrize(
    "filtered_type, other_type",
    [
        ("qa-comment", "reminder"),
        ("report-approved", "reminder"),
        ("reminder", "qa-comment"),
    ],
)
@pytest.mark.django_db
def test_task_list_filter(filtered_type, other_type, rf):
    """Test task list filters"""
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
