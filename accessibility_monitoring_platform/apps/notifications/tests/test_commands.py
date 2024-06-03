"""
Test for email_reminders command
"""

from datetime import date, timedelta

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command

from ...cases.models import Case
from ..models import Task

USER_EMAIL: str = "user@example.com"
USER_FIRST_NAME: str = "Joe"
USER_LAST_NAME: str = "Quimby"
REMINDER_DESCRIPTION_TODAY: str = "Task for today"
REMINDER_DESCRIPTION_TOMORROW: str = "Task for tomorrow"
REMINDER_DESCRIPTION_NO_AUDITOR: str = "Case has no auditor"


@pytest.mark.django_db
def test_email_reminders(mailoutbox):
    """Test email reminders command sends email for reminders due today"""
    user: User = User.objects.create(
        email=USER_EMAIL, first_name=USER_FIRST_NAME, last_name=USER_LAST_NAME
    )
    case: Case = Case.objects.create(auditor=user)
    today: date = date.today()
    tomorrow: date = today + timedelta(days=1)
    Task.objects.create(
        type=Task.Type.REMINDER,
        user=user,
        case=case,
        date=today,
        description=REMINDER_DESCRIPTION_TODAY,
    )
    Task.objects.create(
        type=Task.Type.REMINDER,
        user=user,
        case=case,
        date=tomorrow,
        description=REMINDER_DESCRIPTION_TOMORROW,
    )
    case_without_auditor: Case = Case.objects.create()
    Task.objects.create(
        type=Task.Type.REMINDER,
        user=user,
        case=case_without_auditor,
        date=today,
        description=REMINDER_DESCRIPTION_NO_AUDITOR,
    )

    call_command("email_reminders")

    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [USER_EMAIL]
    assert f"{USER_FIRST_NAME} {USER_LAST_NAME}" in mailoutbox[0].body
    assert REMINDER_DESCRIPTION_TODAY in mailoutbox[0].body
    assert REMINDER_DESCRIPTION_TOMORROW not in mailoutbox[0].body
    assert REMINDER_DESCRIPTION_NO_AUDITOR not in mailoutbox[0].body
