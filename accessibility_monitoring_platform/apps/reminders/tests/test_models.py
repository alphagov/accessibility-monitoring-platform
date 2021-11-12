"""
Test - reminders models
"""
from datetime import date, timedelta

from ..models import Reminder

REMINDER_DESCRIPTION = "Reminder"


def test_past_reminders_are_overdue():
    """Past reminders are overdue"""
    reminder: Reminder = Reminder(due_date=date.today() - timedelta(days=1))
    assert reminder.overdue == True


def test_reminder_due_today_is_not_overdue():
    """Today's reminders are not overdue"""
    reminder: Reminder = Reminder(due_date=date.today())
    assert reminder.overdue == False


def test_reminder_due_in_the_future_is_not_overdue():
    """Future reminders are not overdue"""
    reminder: Reminder = Reminder(due_date=date.today() + timedelta(days=1))
    assert reminder.overdue == False
