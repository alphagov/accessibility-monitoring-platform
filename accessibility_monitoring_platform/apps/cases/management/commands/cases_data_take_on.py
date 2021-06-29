"""
This command adds historic case data.
"""
import csv
from datetime import datetime
from os.path import expanduser
import pytz
import random
import re
from typing import Any, List, Tuple

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import Case, Contact, STATUS_CHOICES

HOME_PATH = expanduser("~")
INPUT_FILE_NAME = f"{HOME_PATH}/historic_cases.csv"

NUMBER_OF_STATUSES: int = len(STATUS_CHOICES)


def extract_data_from_simplified_test_filename(filename: str) -> Tuple[str, str]:
    """Extract Case data from simplified test filename"""
    simplified_test_filename: str = filename.replace("_", "")

    words: List[str] = simplified_test_filename.split(".")[0].split()

    organisation_name = (
        " ".join(words[2:-1]).replace("Simplified Test", "").replace(" Test", "")
    )

    return organisation_name


def extract_data_from_row(row: List[str]) -> Tuple[datetime, str, str, str]:
    """Extract Case data from csv row"""
    yyyy, mm, dd = row["Created date"].split("-")
    created_time = datetime(int(yyyy), int(mm), int(dd), tzinfo=pytz.UTC)

    home_page_url = row["Home page URL"]

    domain_match = re.search("https?://([A-Za-z_0-9.-]+).*", home_page_url)
    domain = domain_match.group(1) if domain_match else ""

    auditor_name = row["Monitored by"]
    test_results_url = row["Link to monitor doc"]
    report_final_url = row["Link to report"]

    return (
        created_time,
        home_page_url,
        domain,
        auditor_name,
        test_results_url,
        report_final_url,
    )


class Command(BaseCommand):
    """
    Command to load historic case data
    """

    help = "Add historic case data to database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            dest="verbose",
            default=False,
            help="Print progress on command line",
        )
        parser.add_argument(
            "--initial",
            action="store_true",
            dest="initial",
            default=False,
            help="Delete existing data",
        )

    def handle(self, *args, **options):
        """
        Reach through historic Case data csv and create entries on database.

        Delete existing Case and Contact data if --initial option is passed.
        """
        verbose: bool = options["verbose"]
        initial: bool = options["initial"]

        if initial:
            if verbose:
                print("Deleting all existing cases and contacts from database")
            Case.objects.all().delete()
            Contact.objects.all().delete()

        users = {
            f"{user.first_name} {user.last_name}": user for user in User.objects.all()
        }
        default_user = User.objects.get(pk=1)
        user_list = list(users.values())
        number_of_users = len(user_list)

        count_report_in_progress_cases = 0

        with open(INPUT_FILE_NAME) as csvfile:
            reader: Any = csv.DictReader(csvfile)
            for count, row in enumerate(reader, start=1):
                try:
                    status = STATUS_CHOICES[random.randint(0, NUMBER_OF_STATUSES)][0]
                    simplified_test_filename = row["Filename"]
                    if verbose:
                        print(f"{count} {simplified_test_filename}")

                    if (
                        row["Created date"] == "Unused"
                        or row["Created date"] == "Missing"
                    ):
                        continue

                    organisation_name = extract_data_from_simplified_test_filename(
                        simplified_test_filename
                    )
                    (
                        created_time,
                        home_page_url,
                        domain,
                        auditor_name,
                        test_results_url,
                        report_final_url,
                    ) = extract_data_from_row(row)

                    auditor = users.get(auditor_name, default_user)
                    created_by = auditor

                    if count % 7:
                        auditor = users.get(auditor_name.strip(), default_user)
                    else:
                        auditor = None

                    if count % 15:
                        reviewer = None
                        if count % 8:
                            report_review_status = "not-started"
                        else:
                            report_review_status = "ready-to-review"
                            status = "report-in-progress"
                    else:
                        reviewer = user_list[count % number_of_users]
                        report_review_status = "ready-to-review"
                        status = "report-in-progress"

                    if count % 4:
                        report_sent_date = None
                    else:
                        report_sent_date = timezone.now()
                        status = "awaiting-response"

                    if count % 6:
                        report_acknowledged_date = None
                    else:
                        report_acknowledged_date = timezone.now()
                        status = "12w-due"

                    if count % 8:
                        compliance_email_sent_date = None
                    else:
                        compliance_email_sent_date = timezone.now()
                        status = "12w-sent"

                    if count % 12:
                        completed = None
                        is_case_completed = False
                    else:
                        completed = timezone.now()
                        is_case_completed = True
                        status = "complete"

                    if count % 100:
                        is_public_sector_body = True
                    else:
                        is_public_sector_body = False
                        status = "not-a-psb"

                    if status == "report-in-progress":
                        count_report_in_progress_cases += 1
                        if count_report_in_progress_cases <= len(user_list):
                            reviewer = user_list[count_report_in_progress_cases]

                    case = Case(
                        id=int(row["Case number"]),
                        organisation_name=organisation_name,
                        home_page_url=home_page_url,
                        domain=domain,
                        auditor=auditor,
                        reviewer=reviewer,
                        simplified_test_filename=row["Filename"],
                        created=created_time,
                        created_by=created_by,
                        status=status,
                        report_review_status=report_review_status,
                        report_sent_date=report_sent_date,
                        report_acknowledged_date=report_acknowledged_date,
                        compliance_email_sent_date=compliance_email_sent_date,
                        is_case_completed=is_case_completed,
                        completed=completed,
                        is_public_sector_body=is_public_sector_body,
                        test_results_url=test_results_url,
                        report_final_url=report_final_url,
                    )
                    case.save()

                    if count % 2:
                        contact = Contact(
                            case=case,
                            first_name="Unknown",
                            last_name="Contact",
                            detail=f"info@{domain}",
                            notes="Fake contact detail",
                            created=created_time,
                            created_by=created_by,
                        )
                        contact.save()

                except Exception as e:
                    print(f"{count} {simplified_test_filename} issue: {str(e)}")
