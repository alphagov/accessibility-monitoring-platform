"""
Test - reminders models
"""
import pytest

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch, Mock

from ...cases.models import Case

from ..models import Reminder

REMINDER_DESCRIPTION = "Reminder"
REMINDER_DUE_DATE: date = date(2022, 1, 1)
DATETIME_REMINDER_UPDATED: datetime = datetime(2021, 9, 27, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "due_date, expected_tense",
    [
        (date.today() - timedelta(days=1), "past"),
        (date.today(), "present"),
        (date.today() + timedelta(days=1), "future"),
    ],
)
def test_reminder_due_date_tense(due_date, expected_tense):
    """Check that the tense is correctly reported"""
    reminder: Reminder = Reminder(due_date=due_date, description=REMINDER_DESCRIPTION)
    assert reminder.tense == expected_tense


@pytest.mark.django_db
def test_reminder_updated_updated():
    """Test the reminder updated field is updated"""
    case: Case = Case.objects.create()
    comment: Reminder = Reminder.objects.create(case=case, due_date=REMINDER_DUE_DATE)

    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_REMINDER_UPDATED)
    ):
        comment.save()

    assert comment.updated == DATETIME_REMINDER_UPDATED
