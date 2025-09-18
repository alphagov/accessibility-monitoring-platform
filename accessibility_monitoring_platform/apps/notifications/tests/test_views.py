"""Test notifications views"""

from datetime import date, timedelta

import pytest
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from ...simplified.models import SimplifiedCase, SimplifiedEventHistory
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
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        base_case=simplified_case,
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
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=other_user)
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=other_user,
        base_case=simplified_case,
    )

    request: HttpRequest = rf.get(
        f'{reverse("notifications:task-list")}?user_id={other_user.id}'
    )
    request.user = request_user

    response: HttpResponse = TaskListView.as_view()(request)

    assert response.status_code == 200
    assertContains(response, "Tasks (1)")


@pytest.mark.django_db
def test_task_list_all_users(rf):
    """Test task list page can show other user's tasks"""
    request_user: User = User.objects.create(
        username="mockuser1", email="mockuser1@mock.com", password="secret1"
    )
    other_user: User = User.objects.create(
        username="mockuser2", email="mockuser2@mock.com", password="secret2"
    )
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=other_user)
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=request_user,
        base_case=simplified_case,
    )
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=other_user,
        base_case=simplified_case,
    )

    request: HttpRequest = rf.get(
        f'{reverse("notifications:task-list")}?show_all_users=true'
    )
    request.user = request_user

    response: HttpResponse = TaskListView.as_view()(request)

    assert response.status_code == 200

    assertContains(response, "Tasks (2)")


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
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    filtered_task: Task = Task.objects.create(
        type=filtered_type,
        date=date.today(),
        user=user,
        base_case=simplified_case,
    )
    other_task: Task = Task.objects.create(
        type=other_type,
        date=date.today(),
        user=user,
        base_case=simplified_case,
    )

    request: HttpRequest = rf.get(
        f'{reverse("notifications:task-list")}?type={filtered_type}'
    )
    request.user = user

    response: HttpResponse = TaskListView.as_view()(request)

    assert response.status_code == 200

    assertContains(response, "Tasks (1)")
    assertContains(
        response,
        f"""<h2 class="govuk-heading-m amp-margin-bottom-20">{filtered_task.get_type_display()}</h2>""",
        html=True,
    )
    assertNotContains(
        response,
        f"""<h2 class="govuk-heading-m amp-margin-bottom-20">{other_task.get_type_display()}</h2>""",
        html=True,
    )


@pytest.mark.parametrize("read_param", ["read", "deleted"])
@pytest.mark.django_db
def test_task_list_read_filter(read_param, rf):
    """Test task list read filter"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        base_case=simplified_case,
        description=DESCRIPTION,
        read=True,
    )
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        base_case=simplified_case,
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
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today() + timedelta(days=7),
        user=user,
        base_case=simplified_case,
        description=DESCRIPTION,
    )
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        base_case=simplified_case,
    )

    request: HttpRequest = rf.get(f'{reverse("notifications:task-list")}?future=true')
    request.user = user

    response: HttpResponse = TaskListView.as_view()(request)

    assert response.status_code == 200

    assertContains(response, "Tasks (1)")
    assertContains(response, DESCRIPTION)


@pytest.mark.django_db
def test_reminder_task_create(admin_client):
    """Test creating a reminder task"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)

    response: HttpResponse = admin_client.post(
        reverse(
            "notifications:reminder-create", kwargs={"case_id": simplified_case.id}
        ),
        {
            "date_0": TODAY.day,
            "date_1": TODAY.month,
            "date_2": TODAY.year,
            "description": DESCRIPTION,
            "save": "Save",
        },
    )

    assert response.status_code == 302

    reminder_task: Task = Task.objects.get(base_case=simplified_case)

    assert reminder_task.description == DESCRIPTION
    assert response.url == reverse(
        "simplified:case-detail", kwargs={"pk": reminder_task.base_case.id}
    )


@pytest.mark.django_db
def test_reminder_task_create_does_not_add_duplicate(admin_client):
    """Test creating a reminder task updates the unread Case reminder if one exists."""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        base_case=simplified_case,
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "notifications:reminder-create", kwargs={"case_id": simplified_case.id}
        ),
        {
            "date_0": TODAY.day,
            "date_1": TODAY.month,
            "date_2": TODAY.year,
            "description": DESCRIPTION,
            "save": "Save",
        },
    )

    assert response.status_code == 302

    assert Task.objects.filter(base_case=simplified_case).count() == 1

    reminder_task: Task = Task.objects.get(base_case=simplified_case)

    assert reminder_task.description == DESCRIPTION


@pytest.mark.django_db
def test_reminder_task_create_adds_reminder_if_no_unread(admin_client):
    """Test creating a reminder task if no unread reminder exists."""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        base_case=simplified_case,
        read=True,
    )

    response: HttpResponse = admin_client.post(
        reverse(
            "notifications:reminder-create", kwargs={"case_id": simplified_case.id}
        ),
        {
            "date_0": TODAY.day,
            "date_1": TODAY.month,
            "date_2": TODAY.year,
            "description": DESCRIPTION,
            "save": "Save",
        },
    )

    assert response.status_code == 302

    assert Task.objects.filter(base_case=simplified_case).count() == 2

    reminder_task: Task = simplified_case.reminder

    assert reminder_task.description == DESCRIPTION


@pytest.mark.django_db
def test_reminder_task_create_redirects_to_case(rf):
    """
    Test creating a reminder task redirects to parent case details
    """
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)

    request: HttpRequest = rf.post(
        reverse(
            "notifications:reminder-create", kwargs={"case_id": simplified_case.id}
        ),
        {
            "date_0": TODAY.day,
            "date_1": TODAY.month,
            "date_2": TODAY.year,
            "description": DESCRIPTION,
            "save": "Save",
        },
    )
    request.user = user

    response: HttpResponse = ReminderTaskCreateView.as_view()(
        request, case_id=simplified_case.id
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "simplified:case-detail", kwargs={"pk": simplified_case.id}
    )

    task: Task = Task.objects.all().first()

    assert task is not None
    assert task.type == Task.Type.REMINDER
    assert task.date == TODAY
    assert task.description == DESCRIPTION

    event_history: SimplifiedEventHistory = SimplifiedEventHistory.objects.all().first()

    assert event_history is not None
    assert event_history.event_type == SimplifiedEventHistory.Type.CREATE


@pytest.mark.django_db
def test_reminder_task_update_redirects_to_self(rf):
    """
    Test updating a reminder task redirects to reminder page
    """
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        base_case=simplified_case,
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
    assert response.url == reverse(
        "notifications:edit-reminder-task", kwargs={"pk": task.id}
    )

    task_from_db: Task = Task.objects.get(id=task.id)

    assert task_from_db is not None
    assert task_from_db.description == DESCRIPTION

    event_history: SimplifiedEventHistory = SimplifiedEventHistory.objects.all().first()

    assert event_history is not None
    assert event_history.event_type == SimplifiedEventHistory.Type.UPDATE


@pytest.mark.django_db
def test_reminder_task_delete_redirects_to_create(rf):
    """
    Test deleting a reminder task redirects to create reminder page
    """
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        base_case=simplified_case,
    )

    request: HttpRequest = rf.post(
        reverse("notifications:edit-reminder-task", kwargs={"pk": task.id}),
        {
            "date_0": TODAY.day,
            "date_1": TODAY.month,
            "date_2": TODAY.year,
            "description": DESCRIPTION,
            "delete": "Delete",
        },
    )
    request.user = user

    response: HttpResponse = ReminderTaskUpdateView.as_view()(request, pk=task.id)

    assert response.status_code == 302
    assert response.url == reverse(
        "notifications:reminder-create", kwargs={"case_id": task.base_case.id}
    )

    task_from_db: Task = Task.objects.get(id=task.id)

    assert task_from_db is not None
    assert task_from_db.read is True

    event_history: SimplifiedEventHistory = SimplifiedEventHistory.objects.all().first()

    assert event_history is not None
    assert event_history.event_type == SimplifiedEventHistory.Type.UPDATE


@pytest.mark.django_db
def test_reminder_task_update_updates_user(rf):
    """
    Test updating a reminder task sets user to match current Case auditor
    """
    user_1: User = User.objects.create(username="user1", email="email1@example.com")
    user_2: User = User.objects.create(username="user2", email="email2@example.com")
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user_2)
    task: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user_1,
        base_case=simplified_case,
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
    request.user = user_2

    response: HttpResponse = ReminderTaskUpdateView.as_view()(request, pk=task.id)

    assert response.status_code == 302

    task_from_db: Task = Task.objects.get(id=task.id)

    assert task_from_db.user == user_2


@pytest.mark.django_db
def test_task_mark_as_read(rf):
    """Test marking task as read"""
    user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.QA_COMMENT,
        date=date.today(),
        user=user,
        base_case=simplified_case,
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
        == f"{task.base_case} {task.get_type_display()} task marked as read"
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
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    qa_comment_task: Task = Task.objects.create(
        type=Task.Type.QA_COMMENT,
        date=date.today(),
        user=user,
        base_case=simplified_case,
    )
    report_approved_task: Task = Task.objects.create(
        type=Task.Type.REPORT_APPROVED,
        date=date.today(),
        user=user,
        base_case=simplified_case,
    )

    request = rf.get(
        reverse(
            "notifications:mark-case-comments-read",
            kwargs={"case_id": simplified_case.id},
        )
    )
    request.user = user
    request._messages = MockMessages()

    assert qa_comment_task.read is False
    assert report_approved_task.read is False

    response: HttpResponse = CommentsMarkAsReadView.as_view()(
        request, case_id=simplified_case.id
    )

    assert response.status_code == 302
    assert response.url == reverse("notifications:task-list")
    assert len(request._messages.messages) == 1
    assert (
        request._messages.messages[0][1] == f"{simplified_case} comments marked as read"
    )

    qa_comment_task_from_db: Task = Task.objects.get(id=qa_comment_task.id)

    assert qa_comment_task_from_db.read is True

    report_approved_task_from_db: Task = Task.objects.get(id=report_approved_task.id)

    assert report_approved_task_from_db.read is True


@pytest.mark.django_db
def test_tast_tools_shown_on_reminder_page(admin_client):
    """Test the reminder page for a simplified case shows the Case tools"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        user=user,
        base_case=simplified_case,
    )

    response: HttpResponse = admin_client.get(
        reverse("notifications:edit-reminder-task", kwargs={"pk": task.id}),
    )

    assert response.status_code == 200

    assertContains(
        response, '<h2 class="govuk-heading-s amp-margin-bottom-10">Case tools</h2>'
    )


@pytest.mark.django_db
def test_deactivate_case_updates_status(admin_client):
    """Test deactivating a case updates its status to deactivated"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.status == SimplifiedCase.Status.UNASSIGNED

    response: HttpResponse = admin_client.post(
        reverse("simplified:deactivate-case", kwargs={"pk": simplified_case.id}),
        {
            "version": simplified_case.version,
            "deactivate_notes": "Deactivate note",
            "deactivate": "Deactivate case",
        },
    )

    assert response.status_code == 302

    simplified_case_from_db: SimplifiedCase = SimplifiedCase.objects.get(
        id=simplified_case.id
    )

    assert simplified_case_from_db.status == SimplifiedCase.Status.DEACTIVATED
