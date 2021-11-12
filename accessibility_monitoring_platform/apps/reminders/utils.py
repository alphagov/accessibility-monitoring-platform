"""Utilitiy functions for reminders """
from datetime import date

from django.contrib.auth.models import User

from .models import Reminder


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
