"""
This command emails reminders due today to their user.
"""
from datetime import date
from typing import Dict, List, TypedDict

from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.db.models.query import QuerySet
from django.template.loader import get_template

from ...models import Reminder


class EmailContextType(TypedDict):
    user: User
    reminders: List[Reminder]


class Command(BaseCommand):
    """
    Command to email today's reminders to their user.
    """

    help = "Email today's reminders to their user."

    def handle(self, *args, **options):
        """
        Find reminders due today, group them by user, and email them to their user.
        """
        reminders: QuerySet[Reminder] = Reminder.objects.filter(due_date=date.today())
        reminders_by_user: Dict[User, List[Reminder]] = {}
        for reminder in reminders:
            reminders_by_user.setdefault(reminder.user, []).append(reminder)

        for user, user_reminders in reminders_by_user.items():
            context: EmailContextType = {
                "user": user,
                "reminders": user_reminders,
            }
            template: str = get_template("reminders/email.txt")
            content: str = template.render(context)  # type: ignore
            email: EmailMessage = EmailMessage(
                subject="You have a reminder in the monitoring platform",
                body=content,
                from_email="accessibility-monitoring-platform-contact-form@digital.cabinet-office.gov.uk",
                to=[user.email],
            )
            email.content_subtype = "html"
            email.send()
