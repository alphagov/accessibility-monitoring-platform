"""
This command populates the followup and chaser dates of cases.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand

from ...models import Case
from ...views import ONE_WEEK_IN_DAYS, FOUR_WEEKS_IN_DAYS, TWELVE_WEEKS_IN_DAYS


class Command(BaseCommand):
    """
    Command to populate foloowup and chaser dates
    """

    help = "Add historic case data to database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Save no changes",
        )

    def handle(self, *args, **options):
        """
        Read through all the cases, check for dates and populate missing ones.
        """
        dry_run: bool = options["dry_run"]

        for case in Case.objects.all():
            case_updated: bool = False
            if case.report_sent_date:
                if case.report_followup_week_1_due_date is None:
                    case.report_followup_week_1_due_date = (
                        case.report_sent_date + timedelta(days=ONE_WEEK_IN_DAYS)
                    )
                    case_updated = True
                if case.report_followup_week_4_due_date is None:
                    case.report_followup_week_4_due_date = (
                        case.report_sent_date + timedelta(days=FOUR_WEEKS_IN_DAYS)
                    )
                    case_updated = True
                if case.report_followup_week_12_due_date is None:
                    case.report_followup_week_12_due_date = (
                        case.report_sent_date + timedelta(days=TWELVE_WEEKS_IN_DAYS)
                    )
                    case_updated = True

            if case.twelve_week_update_requested_date:
                if case.twelve_week_1_week_chaser_due_date is None:
                    case.twelve_week_1_week_chaser_due_date = (
                        case.twelve_week_update_requested_date
                        + timedelta(days=ONE_WEEK_IN_DAYS)
                    )
                    case_updated = True
                if case.twelve_week_4_week_chaser_due_date is None:
                    case.twelve_week_4_week_chaser_due_date = (
                        case.twelve_week_update_requested_date
                        + timedelta(days=FOUR_WEEKS_IN_DAYS)
                    )
                    case_updated = True

            if case_updated and not dry_run:
                case.save()
