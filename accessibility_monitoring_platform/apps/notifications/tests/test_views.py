"""Test notifications views"""

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains

from ...cases.models import Case
from ..models import Task
from ..views import TaskListView


@pytest.mark.django_db
def test_empty_task_list(rf):
    """Test empty task list page renders"""
    user: User = User.objects.create()
    case: Case = Case.objects.create(auditor=user)

    request: HttpRequest = rf.get(reverse("notifications:task-list"))
    request.user = user

    response: HttpResponse = TaskListView.as_view()(request, pk=case.id)
    case: Case = Case.objects.create()

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

    response: HttpResponse = TaskListView.as_view()(request, pk=case.id)
    case: Case = Case.objects.create()

    assert response.status_code == 200
    assertContains(response, "Tasks (1)")
