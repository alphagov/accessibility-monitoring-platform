"""Reset test data in the database"""
from typing import List

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

from ....audits.models import Audit, CheckResult, Page, WcagDefinition
from ....cases.models import Case, Contact
from ....comments.models import Comment, CommentHistory
from ....notifications.models import Notification, NotificationSetting
from ....reminders.models import Reminder
from ....reports.models import (
    Report,
    ReportFeedback,
    ReportVisitsMetrics,
    BaseTemplate,
    ReportWrapper,
    Section,
    TableRow,
)
from ....s3_read_write.models import S3Report

from ...models import ChangeToPlatform, Event, IssueReport, Platform, Sector


def load_fixture(fixture: str) -> None:
    """Load data from fixture into database"""
    fixture_path: str = f"cypress/fixtures/{fixture}.json"
    print(f"Loading fixture from {fixture_path}:")
    call_command("loaddata", fixture_path)


def delete_from_models(model_classes) -> None:
    """Delete all data from models"""
    for model_class in model_classes:
        model_class.objects.all().delete()


def delete_from_tables(table_names: List[str]) -> None:
    """Delete data from tables"""
    with connection.cursor() as cursor:
        for table_name in table_names:
            print(f"Deleting data from table {table_name}")
            cursor.execute(f"DELETE FROM {table_name}")


class Command(BaseCommand):
    """Django command to reset the database"""

    def handle(self, *args, **options):
        # Reset audits data
        delete_from_models([CheckResult, Page, Audit, WcagDefinition])
        load_fixture("wcag_definition")

        # Delete Axes (access) data
        delete_from_tables(
            ["axes_accesslog", "axes_accessattempt", "axes_accessfailurelog"]
        )

        # Delete comments data
        delete_from_models([CommentHistory, Comment])

        # Delete notifications data
        delete_from_models([Notification, NotificationSetting])

        # Delete one-time token data
        delete_from_tables(
            [
                "otp_email_emaildevice",
                "otp_static_staticdevice",
                "otp_static_statictoken",
                "otp_totp_totpdevice",
            ]
        )

        # Delete s3_read_write data
        delete_from_models([S3Report])

        # Delete cases data
        delete_from_models([Contact, Case])

        # Reset common data
        delete_from_models([ChangeToPlatform, Event, IssueReport, Platform, Sector])
        load_fixture("sector")

        # Reset common data
        delete_from_models(
            [
                BaseTemplate,
                ReportWrapper,
                ReportFeedback,
                ReportVisitsMetrics,
                TableRow,
                Section,
                Report,
            ]
        )
        load_fixture("base_template")
        load_fixture("report_wrapper")

        # Delete reminders data
        delete_from_models([Reminder])

        # Reset user data
        delete_from_models([Group, User])
        load_fixture("group")
        load_fixture("user")
        load_fixture("platform_settings")

        # Reset case data
        load_fixture("case")
