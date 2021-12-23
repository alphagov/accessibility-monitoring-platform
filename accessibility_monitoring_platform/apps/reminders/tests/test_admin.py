"""
Test - common admin actions
"""
import csv
import io
from datetime import date

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse

from ...cases.models import Case
from ..models import Reminder

REMINDER_DESCRIPTION_1: str = "Reminder One"
REMINDER_DESCRIPTION_2: str = "Reminder Two"


def test_reminder_export_as_csv(admin_client):
    """Test action to export reminders as csv"""
    user: User = User.objects.create()
    case: Case = Case.objects.create()
    today: date = date.today()
    reminder_1: Reminder = Reminder.objects.create(
        case=case, user=user, due_date=today, description=REMINDER_DESCRIPTION_1
    )
    reminder_2: Reminder = Reminder.objects.create(
        case=case, user=user, due_date=today, description=REMINDER_DESCRIPTION_2
    )

    response: HttpResponse = admin_client.post(
        reverse("admin:reminders_reminder_changelist"),
        {
            "action": "export_as_csv",
            "_selected_action": [reminder_1.id, reminder_2.id],  # type: ignore
        },
    )

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    cvs_reader = csv.reader(io.StringIO(content))
    rows = list(cvs_reader)

    assert len(rows) == 3
    assert rows[0] == ["id", "case", "user", "due_date", "description", "is_deleted"]
    assert rows[1][3] == str(today)
    assert rows[1][4] == REMINDER_DESCRIPTION_2
    assert rows[2][3] == str(today)
    assert rows[2][4] == REMINDER_DESCRIPTION_1
