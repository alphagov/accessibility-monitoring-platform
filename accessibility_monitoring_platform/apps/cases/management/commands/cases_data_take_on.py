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

from django.core.management.base import BaseCommand

from ...models import Case, Contact, STATUS_CHOICES

AUDITORS = {
    "AH": "Andrew Hick",
    "JE": "Jessica Eley",
    "KB": "Katherine Badger",
    "KC": "Kelly Clarkson",
    "KR": "Keeley Robertson",
    "NR": "Nesha Russo",
}

HOME_PATH = expanduser("~")
INPUT_FILE_NAME = f"{HOME_PATH}/historic_cases.csv"

NUMBER_OF_STATUSES: int = len(STATUS_CHOICES)


def extract_data_from_simplified_test_filename(filename: str) -> Tuple[str, str]:
    """ Extract Case data from simplified test filename """
    simplified_test_filename: str = filename.replace("_", "")

    words: List[str] = simplified_test_filename.split(".")[0].split()

    auditor_initials = words[-1]
    organisation_name = (
        " ".join(words[2:-1]).replace("Simplified Test", "").replace(" Test", "")
    )

    return (auditor_initials, organisation_name)


def extract_data_from_row(row: List[str]) -> Tuple[datetime, str, str, str]:
    """ Extract Case data from csv row """
    yyyy, mm, dd = row["Created date"].split("-")
    created_time = datetime(int(yyyy), int(mm), int(dd), tzinfo=pytz.UTC)

    home_page_url = row["Home page URL"]

    domain_match = re.search("https?://([A-Za-z_0-9.-]+).*", home_page_url)
    domain = domain_match.group(1) if domain_match else ""

    status = STATUS_CHOICES[random.randint(0, NUMBER_OF_STATUSES)][0]
    if not status:
        status = "test-in-progress"

    return (created_time, home_page_url, domain, status)


class Command(BaseCommand):
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

        with open(INPUT_FILE_NAME) as csvfile:
            reader: Any = csv.DictReader(csvfile)
            for count, row in enumerate(reader, start=1):
                try:
                    simplified_test_filename = row["Filename"]
                    if verbose:
                        print(f"{count} {simplified_test_filename}")

                    if (
                        row["Created date"] == "Unused"
                        or row["Created date"] == "Missing"
                    ):
                        continue

                    (
                        auditor_initials,
                        organisation_name,
                    ) = extract_data_from_simplified_test_filename(
                        simplified_test_filename
                    )
                    created_time, home_page_url, domain, status = extract_data_from_row(
                        row
                    )

                    case = Case(
                        id=int(row["Case number"]),
                        organisation_name=organisation_name,
                        home_page_url=home_page_url,
                        domain=domain,
                        auditor=AUDITORS[auditor_initials],
                        simplified_test_filename=row["Filename"],
                        created=created_time,
                        created_by=AUDITORS[auditor_initials],
                        status=status,
                    )
                    case.save()

                    if "Contact name" in row and row["Contact name"]:
                        name_words = row["Contact name"].split()
                        contact = Contact(
                            case=case,
                            first_name=name_words[0],
                            last_name=" ".join(name_words[1:]),
                            job_title=row["Job title"],
                            detail=row["Contact detail"].split("\n")[0],
                            notes=row["Contact detail"],
                            created=created_time,
                            created_by=AUDITORS[auditor_initials],
                        )
                        contact.save()

                except Exception as e:
                    print(f"{count} {simplified_test_filename} issue: {str(e)}")
