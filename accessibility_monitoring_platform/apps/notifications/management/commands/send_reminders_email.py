"""Command to send reminders email"""

import os

from django.core.management.base import BaseCommand
from ...utils import email_all_specialists_all_detailed_reminders_due


class Command(BaseCommand):
    def handle(self, *args, **options):  # pylint: disable=unused-argument
        if os.getenv("COPILOT_ENVIRONMENT_NAME") == "prodenv":
            email_all_specialists_all_detailed_reminders_due()
