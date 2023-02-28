"""
Test for loat_test_cases_csv command
"""
import pytest

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management import call_command

from ...cases.models import Case
from ..models import Reminder

USER_EMAIL = "user@example.com"
USER_FIRST_NAME = "Joe"
USER_LAST_NAME = "Quimby"
REMINDER_DESCRIPTION_TODAY = "Reminder for today"
REMINDER_DESCRIPTION_TOMORROW = "Reminder for tomorrow"


@pytest.mark.django_db
def test_email_reminders(mailoutbox):
    """Test email reminders command sends email for reminders due today"""
    user: User = User.objects.create(
        email=USER_EMAIL, first_name=USER_FIRST_NAME, last_name=USER_LAST_NAME
    )
    case: Case = Case.objects.create(auditor=user)
    today: date = date.today()
    tomorrow: date = today + timedelta(days=1)
    Reminder.objects.create(
        case=case, due_date=today, description=REMINDER_DESCRIPTION_TODAY,
    )
    Reminder.objects.create(
        case=case,
        due_date=tomorrow,
        description=REMINDER_DESCRIPTION_TOMORROW,
    )

    call_command("email_reminders")

    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [USER_EMAIL]
    assert f"{USER_FIRST_NAME} {USER_LAST_NAME}" in mailoutbox[0].body
    assert REMINDER_DESCRIPTION_TODAY in mailoutbox[0].body
    assert REMINDER_DESCRIPTION_TOMORROW not in mailoutbox[0].body
