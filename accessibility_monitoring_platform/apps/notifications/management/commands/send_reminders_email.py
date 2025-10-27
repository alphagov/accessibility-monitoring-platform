"""Command to send reminders email"""

from django.core.management.base import BaseCommand
from ...utils import email_all_specialists_all_detailed_reminders_due


class Command(BaseCommand):
    def handle(self, *args, **options):  # pylint: disable=unused-argument
        email_all_specialists_all_detailed_reminders_due()
