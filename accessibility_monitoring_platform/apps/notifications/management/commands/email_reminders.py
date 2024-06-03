"""
This command emails reminders due today to their user.
"""

from datetime import date
from typing import Dict, List, TypedDict

from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.template.loader import get_template

from ...models import Task


class EmailContextType(TypedDict):
    user: User
    reminders: List[Task]


class Command(BaseCommand):
    """
    Command to email today's reminders to their user.
    """

    help = "Email today's reminders to their user."

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """
        Find reminders due today, group them by user, and email them to their user.
        """
        tasks: Task = Task.objects.filter(date=date.today(), type=Task.Type.REMINDER)
        tasks_by_user: Dict[User, List[Task]] = {}
        for task in tasks:
            user: User = task.case.auditor
            if user is None:
                continue
            if user in tasks_by_user:
                tasks_by_user[user].append(task)
            else:
                tasks_by_user[user] = [task]

        for user, user_tasks in tasks_by_user.items():
            context: EmailContextType = {
                "user": user,
                "tasks": user_tasks,
            }
            template: str = get_template("notifications/reminder_email.txt")
            content: str = template.render(context)
            email: EmailMessage = EmailMessage(
                subject="You have a reminder in the monitoring platform",
                body=content,
                from_email="accessibility-monitoring-platform-contact-form@digital.cabinet-office.gov.uk",
                to=[user.email],
            )
            email.content_subtype = "html"
            email.send()
