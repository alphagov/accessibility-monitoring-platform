"""Utilitiy functions for reminders """
from datetime import date
from typing import Any, Dict

from django.contrib.auth.models import User

from ..cases.models import Case
from .models import Reminder

REMINDER_PAGE_HEADING: str = "Edit case | Reminder"


def get_number_of_reminders_for_user(user: User) -> int:
    """
    Check that the user is not anonymous (i.e. logged in) and return the
    number of their reminders which are due or overdue.
    """
    if user.id:  # type: ignore
        today: date = date.today()
        return Reminder.objects.filter(
            is_deleted=False, user=user, due_date__lte=today
        ).count()
    return 0


def add_reminder_context_data(context: Dict[str, Any], case_id: int) -> Dict[str, Any]:
    """Add reminder data to context"""

    case: Case = Case.objects.get(pk=case_id)
    context["case"] = case
    context["page_heading"] = REMINDER_PAGE_HEADING
    context["page_title"] = f"{case.organisation_name} | {REMINDER_PAGE_HEADING}"
    return context
