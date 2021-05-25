"""
This command adds historic case data.
"""
import csv
from datetime import datetime
import pytz

from django.core.management.base import BaseCommand

from ...models import Case

INPUT_FILE_NAME = "home_page_urls.csv"
AUDITORS = {
    "AH": "Andrew Hick",
    "JE": "Jessica Eley",
    "KB": "Katherine Badger",
    "KR": "Keeley Robertson",
    "NR": "Nesha Russo",
}


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
        verbose = options["verbose"]
        initial = options["initial"]

        if initial:
            if verbose:
                print("Deleting all existing cases from database")
            Case.objects.all().delete()

        with open(INPUT_FILE_NAME) as csvfile:
            reader = csv.DictReader(csvfile)
            for count, row in enumerate(reader, start=1):
                try:
                    simplified_test_filename = row["Filename"].replace("_", "")
                    if verbose:
                        print(f"{count} {simplified_test_filename}")
                    if row["Created date"] == "Unused" or row["Created date"] == "Missing":
                        continue
                    words = simplified_test_filename.split(".")[0].split()
                    auditor_initials = words[-1]
                    website_name = " ".join(words[2:-1])
                    yyyy, mm, dd = row["Created date"].split("-")
                    case = Case(
                        id=int(row["Case number"]),
                        website_name=website_name,
                        home_page_url=row["URL"],
                        auditor=AUDITORS[auditor_initials],
                        simplified_test_filename=row["Filename"],
                        created=datetime(int(yyyy), int(mm), int(dd), tzinfo=pytz.UTC),
                        created_by=AUDITORS[auditor_initials],
                    )
                    case.save()
                except Exception as e:
                    print(f"{count} {simplified_test_filename} issue: {str(e)}")
