"""
Tests for reminders views
"""
from datetime import date

import pytest
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from ...cases.models import Case
from ..models import Reminder

REMINDER_DUE_DATE: date = date(2021, 4, 1)
REMINDER_DESCRIPTION: str = "Reminder description"
NEW_REMINDER_DESCRIPTION: str = "New reminder description"


@pytest.fixture
def client_and_user(client, django_user_model):
    username = "foo"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    client.force_login(user)
    return client, user


def test_create_reminder(client_and_user):  # pylint: disable=redefined-outer-name
    """
    Test that reminder can be created
    """
    client, user = client_and_user
    case: Case = Case.objects.create(auditor=user)

    response: HttpResponse = client.post(
        reverse("reminders:reminder-create", kwargs={"case_id": case.id}),
        {
            "due_date_0": REMINDER_DUE_DATE.day,
            "due_date_1": REMINDER_DUE_DATE.month,
            "due_date_2": REMINDER_DUE_DATE.year,
            "description": REMINDER_DESCRIPTION,
            "save_exit": "Save and exit",
        },
    )

    assert response.status_code == 302
    updated_case: Case = Case.objects.get(pk=case.id)

    assert updated_case.reminder is not None
    assert updated_case.reminder.due_date == REMINDER_DUE_DATE
    assert updated_case.reminder.description == REMINDER_DESCRIPTION
    assert updated_case.reminder.case.auditor == user


def test_update_reminder(client_and_user):  # pylint: disable=redefined-outer-name
    """
    Test that reminder can be updated
    """
    client, user = client_and_user
    case: Case = Case.objects.create(auditor=user)
    reminder: Reminder = Reminder.objects.create(
        case=case,
        due_date=REMINDER_DUE_DATE,
        description=REMINDER_DESCRIPTION,
    )

    response: HttpResponse = client.post(
        reverse("reminders:edit-reminder", kwargs={"pk": reminder.id}),
        {
            "due_date_0": REMINDER_DUE_DATE.day,
            "due_date_1": REMINDER_DUE_DATE.month,
            "due_date_2": REMINDER_DUE_DATE.year,
            "description": NEW_REMINDER_DESCRIPTION,
            "save_exit": "Save and exit",
        },
    )

    assert response.status_code == 302
    updated_case: Case = Case.objects.get(pk=case.id)

    assert updated_case.reminder is not None
    assert updated_case.reminder.description == NEW_REMINDER_DESCRIPTION


def test_reminders_for_user_listed(
    client_and_user,
):  # pylint: disable=redefined-outer-name
    """
    Test that reminders in cases where the logged in user is the auditor are listed.
    """
    client, user = client_and_user
    case_1: Case = Case.objects.create(auditor=user)
    Reminder.objects.create(
        case=case_1,
        due_date=REMINDER_DUE_DATE,
        description=REMINDER_DESCRIPTION,
    )
    case_2: Case = Case.objects.create(auditor=user)
    Reminder.objects.create(
        case=case_2,
        due_date=date.today(),
        description=NEW_REMINDER_DESCRIPTION,
    )

    response: HttpResponse = client.get(reverse("reminders:reminder-list"))

    assert response.status_code == 200
    assertContains(response, "Reminders (2)")
    assertContains(response, REMINDER_DESCRIPTION)
    assertContains(response, NEW_REMINDER_DESCRIPTION)


def test_delete_reminder(client_and_user):  # pylint: disable=redefined-outer-name
    """
    Test that reminder can be deleted
    """
    client, user = client_and_user
    case: Case = Case.objects.create(auditor=user)
    reminder: Reminder = Reminder.objects.create(
        case=case,
        due_date=REMINDER_DUE_DATE,
        description=REMINDER_DESCRIPTION,
    )

    response: HttpResponse = client.get(
        reverse("reminders:delete-reminder", kwargs={"pk": reminder.id}),
    )

    assert response.status_code == 302

    deleted_reminder: Reminder = Reminder.objects.get(pk=reminder.id)
    assert deleted_reminder.is_deleted

    updated_case: Case = Case.objects.get(pk=case.id)
    assert updated_case.reminder is None


def test_updating_auditor_changes_reminders_listed(
    client_and_user,
):  # pylint: disable=redefined-outer-name
    """
    Test that updating the case auditor changes the listed reminders.
    """
    client, user = client_and_user
    case_1: Case = Case.objects.create(auditor=user)
    Reminder.objects.create(
        case=case_1,
        due_date=REMINDER_DUE_DATE,
        description=REMINDER_DESCRIPTION,
    )
    case_2: Case = Case.objects.create()
    Reminder.objects.create(
        case=case_2,
        due_date=date.today(),
        description=NEW_REMINDER_DESCRIPTION,
    )

    response: HttpResponse = client.get(reverse("reminders:reminder-list"))

    assert response.status_code == 200
    assertContains(response, "Reminders (1)")
    assertContains(response, REMINDER_DESCRIPTION)
    assertNotContains(response, NEW_REMINDER_DESCRIPTION)

    case_2.auditor = user
    case_2.save()

    response: HttpResponse = client.get(reverse("reminders:reminder-list"))

    assert response.status_code == 200
    assertContains(response, "Reminders (2)")
    assertContains(response, REMINDER_DESCRIPTION)
    assertContains(response, NEW_REMINDER_DESCRIPTION)
