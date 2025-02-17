"""Reset integration test data in the database"""

import logging

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection, models
from django.db.utils import OperationalError

from accessibility_monitoring_platform.apps.common.models import (
    FrequentlyUsedLink,
    UserCacheUniqueHash,
)

from ....audits.models import (
    Audit,
    CheckResult,
    Page,
    Retest,
    RetestCheckResult,
    RetestPage,
    RetestStatementCheckResult,
    StatementCheck,
    StatementCheckResult,
    StatementPage,
    WcagDefinition,
)
from ....cases.models import (
    Case,
    CaseCompliance,
    CaseEvent,
    CaseNoteHistory,
    CaseStatus,
    Contact,
    EqualityBodyCorrespondence,
    ZendeskTicket,
)
from ....comments.models import Comment
from ....common.models import EmailTemplate
from ....exports.models import Export, ExportCase
from ....notifications.models import NotificationSetting, Task
from ....reports.models import Report, ReportVisitsMetrics, ReportWrapper
from ....s3_read_write.models import S3Report
from ....users.models import AllowedEmail
from ...models import ChangeToPlatform, Event, IssueReport, Platform, Sector


def load_fixture(fixture: str) -> None:
    """Load data from fixture into database"""
    fixture_path: str = f"stack_tests/integration_tests/fixtures/{fixture}.json"
    print(f"Loading {fixture_path}")
    logging.info("Loading fixture from %s:", fixture_path)
    call_command("loaddata", fixture_path)


def delete_from_models(model_classes: list[type[models.Model]]) -> None:
    """Delete all data from models"""
    for model_class in model_classes:
        logging.info("Deleting data from model %s", model_class)
        model_class.objects.all().delete()


def delete_from_tables(table_names: list[str]) -> None:
    """Delete data from tables"""
    with connection.cursor() as cursor:
        for table_name in table_names:
            logging.info("Deleting data from table %s", table_name)
            try:
                cursor.execute(f"DELETE FROM {table_name}")
            except OperationalError:  # Tables don't exist in unit test environment
                pass


class Command(BaseCommand):
    """Django command to reset the database"""

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """Reset database for integration tests"""

        delete_from_models(
            [
                Task,
                EmailTemplate,
                ExportCase,
                Export,
                ZendeskTicket,
                StatementPage,
                FrequentlyUsedLink,
                EqualityBodyCorrespondence,
                RetestStatementCheckResult,
                RetestCheckResult,
                RetestPage,
                Retest,
                StatementCheckResult,
                CheckResult,
                Page,
                Audit,
                StatementCheck,
                WcagDefinition,
                UserCacheUniqueHash,
                CaseCompliance,
                CaseNoteHistory,
                CaseStatus,
            ]
        )
        delete_from_tables(
            ["axes_accesslog", "axes_accessattempt", "axes_accessfailurelog"]
        )  # Axes (access)
        delete_from_models([Comment])
        delete_from_models([NotificationSetting])
        delete_from_tables(
            [
                "otp_email_emaildevice",
                "otp_static_staticdevice",
                "otp_static_statictoken",
                "otp_totp_totpdevice",
            ]
        )  # One-time token
        delete_from_models([S3Report])
        delete_from_models(
            [
                ReportWrapper,
                ReportVisitsMetrics,
                Report,
            ]
        )
        delete_from_models([Contact, CaseEvent, Case])
        delete_from_models(
            [ChangeToPlatform, Event, IssueReport, Platform, Sector]
        )  # Common
        delete_from_models([Group, User])
        delete_from_models([AllowedEmail])

        load_fixture("wcag_definition")
        load_fixture("statementcheck")
        load_fixture("report_wrapper")  # Report UI text
        load_fixture("sector")
        load_fixture("allowed_email")
        load_fixture("group")
        load_fixture("user")
        load_fixture("emailtemplate")
        load_fixture("platform_settings")
        load_fixture("case")
        load_fixture("contact")
        load_fixture("audits")  # Test results
        load_fixture("statementcheckresult")
        load_fixture("reports")  # Reports
        load_fixture("s3_report")  # Published report
