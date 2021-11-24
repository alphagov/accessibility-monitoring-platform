"""
Test - reminders models
"""
import pytest

from datetime import date, timedelta

from ..models import Reminder

REMINDER_DESCRIPTION = "Reminder"


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
