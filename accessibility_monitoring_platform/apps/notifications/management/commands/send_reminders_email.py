"""Command to send reminders email"""

import os

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...utils import email_all_specialists_all_detailed_reminders_due

DAY_OF_WEEK_MONDAY: int = 0


class Command(BaseCommand):
    def handle(self, *args, **options):  # pylint: disable=unused-argument
        if (
            os.getenv("COPILOT_ENVIRONMENT_NAME") == "prodenv"
            and timezone.now().weekday() == DAY_OF_WEEK_MONDAY
        ):
            email_all_specialists_all_detailed_reminders_due()
