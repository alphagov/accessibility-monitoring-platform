"""
This command adds historic case data.
"""
import csv
from datetime import date, datetime
from typing import Any, Dict, List, Union

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ...models import Case, Contact
from ....common.models import Region, Sector

INPUT_FILE_NAME = (
    "accessibility_monitoring_platform/apps/cases/management/commands/test_cases.csv"
)


def delete_existing_data(verbose) -> None:
    if verbose:
        print("Deleting all existing cases and contacts from database")
    Case.objects.all().delete()
    Contact.objects.all().delete()


def get_users() -> Dict[str, User]:
    return {user.username: user for user in User.objects.all()}


def get_regions() -> Dict[str, Region]:
    return {region.name: region for region in Region.objects.all()}


def get_sectors() -> Dict[str, Sector]:
    return {sector.name: sector for sector in Sector.objects.all()}


def get_boolean_from_row(row: List[str], fieldname: str) -> str:
    string = row.get(fieldname, "")
    if string == "":
        return None
    return string == "True"


def get_string_from_row(row: List[str], fieldname: str) -> str:
    return row.get(fieldname, "")


def get_id_from_row(row: List[str]) -> int:
    id = row.get("id")
    return int(id)


def get_user_from_row(
    row: List[str], users: List[User], fieldname: str
) -> Union[User, None]:
    user_email = row.get(fieldname)
    return users.get(user_email) if user_email is not None else None


def get_date_from_row(row: List[str], fieldname: str) -> Union[date, None]:
    date_string: Union[str, None] = row.get(fieldname)
    if date_string:
        yyyy, mm, dd = date_string.split("-")
        return date(int(yyyy), int(mm), int(dd))
    return None


def get_datetime_from_row(row: List[str], fieldname: str) -> Union[datetime, None]:
    datetime_string: Union[str, None] = row.get(fieldname)
    if datetime_string:
        try:
            timestamp = datetime.strptime(datetime_string, "%Y-%m-%d %H:%M:%S.%f+00:00")
        except ValueError:
            timestamp = datetime.strptime(datetime_string, "%Y-%m-%d %H:%M:%S+00:00")
        return timestamp
    return None


def get_status_from_row(row: List[str]) -> str:
    return row.get("status", "new-case")


def get_test_type_from_row(row: List[str]) -> str:
    return row.get("test_type", "simple")


def get_website_type_from_row(row: List[str]) -> str:
    return row.get("website_type", "public")


def get_sector_from_row(
    row: List[str], sectors: Dict[str, Sector]
) -> Union[Sector, None]:
    sector_name = row.get("sector")
    if sector_name:
        return sectors.get(sector_name)
    return None


def get_regions_from_row(row: List[str], regions) -> List[Region]:
    region = row.get("region", None)
    if region is not None:
        region_names = region.split(",")
        return [
            regions[region_name]
            for region_name in region_names
            if region_name in regions
        ]
    return []


def get_case_origin_from_row(row: List[str]) -> str:
    return row.get("case_origin", "org")


def get_test_status_from_row(row: List[str]) -> str:
    return row.get("test_status", "not-started")


def get_report_review_status_from_row(row: List[str]) -> str:
    return row.get("report_review_status", "not-started")


def get_report_approved_status_from_row(row: List[str]) -> str:
    return row.get("report_approved_status", "not-started")


def get_accessibility_statement_decison_from_row(row: List[str]) -> str:
    return row.get("accessibility_statement_decison", "not-compliant")


def get_compliance_decision_from_row(row: List[str]) -> str:
    return row.get("compliance_decision", "unknown")


def create_case(
    row: List[str],
    users: Dict[str, User],
    regions: Dict[str, Region],
    sectors: Dict[str, Sector],
) -> Case:
    return Case.objects.create(
        id=get_id_from_row(row),
        status=get_status_from_row(row),
        created=get_datetime_from_row(row, "created"),
        auditor=get_user_from_row(row, users, "auditor"),
        test_type=get_test_type_from_row(row),
        home_page_url=get_string_from_row(row, "home_page_url"),
        domain=get_string_from_row(row, "domain"),
        application=get_string_from_row(row, "application"),
        organisation_name=get_string_from_row(row, "organisation_name"),
        website_type=get_website_type_from_row(row),
        sector=get_sector_from_row(row, sectors),
        case_origin=get_case_origin_from_row(row),
        zendesk_url=get_string_from_row(row, "zendesk_url"),
        trello_url=get_string_from_row(row, "trello_url"),
        notes=get_string_from_row(row, "notes"),
        is_public_sector_body=get_boolean_from_row(row, "is_public_sector_body"),
        test_results_url=get_string_from_row(row, "test_results_url"),
        test_status=get_test_status_from_row(row),
        is_website_compliant=get_boolean_from_row(row, "is_website_compliant"),
        test_notes=get_string_from_row(row, "test_notes"),
        report_draft_url=get_string_from_row(row, "report_draft_url"),
        report_review_status=get_report_review_status_from_row(row),
        reviewer=get_user_from_row(row, users, "reviewer"),
        report_approved_status=get_report_approved_status_from_row(row),
        reviewer_notes=get_string_from_row(row, "reviewer_notes"),
        report_final_url=get_string_from_row(row, "report_final_url"),
        report_sent_date=get_date_from_row(row, "report_sent_date"),
        report_acknowledged_date=get_date_from_row(row, "report_acknowledged_date"),
        week_12_followup_date=get_date_from_row(row, "week_12_followup_date"),
        psb_progress_notes=get_string_from_row(row, "psb_progress_notes"),
        week_12_followup_email_sent_date=get_date_from_row(
            row, "week_12_followup_email_sent_date"
        ),
        week_12_followup_email_acknowledgement_date=get_date_from_row(
            row, "week_12_followup_email_acknowledgement_date"
        ),
        is_website_retested=get_boolean_from_row(row, "is_website_retested"),
        is_disproportionate_claimed=get_boolean_from_row(
            row, "is_disproportionate_claimed"
        ),
        disproportionate_notes=get_string_from_row(row, "disproportionate_notes"),
        accessibility_statement_decison=get_accessibility_statement_decison_from_row(
            row
        ),
        accessibility_statement_url=get_string_from_row(
            row, "accessibility_statement_url"
        ),
        accessibility_statement_notes=get_string_from_row(
            row, "accessibility_statement_notes"
        ),
        compliance_decision=get_compliance_decision_from_row(row),
        compliance_decision_notes=get_string_from_row(row, "compliance_decision_notes"),
        compliance_email_sent_date=get_date_from_row(row, "compliance_email_sent_date"),
        sent_to_enforcement_body_sent_date=get_date_from_row(
            row, "sent_to_enforcement_body_sent_date"
        ),
        is_case_completed=get_boolean_from_row(row, "is_case_completed"),
        completed=get_datetime_from_row(row, "completed"),
        is_archived=get_boolean_from_row(row, "is_archived"),
    )


class Command(BaseCommand):
    """
    Command to load Case and Contact test data from csv
    """

    help = "Add Case and Contact test data to database."

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
        Reach through Case test data csv and create entries on database.

        Delete existing Case and Contact data if --initial option is passed.
        """
        verbose: bool = options["verbose"]
        initial: bool = options["initial"]

        if initial:
            delete_existing_data(verbose)

        regions: Dict[str, Region] = get_regions()
        sectors: Dict[str, Sector] = get_sectors()
        users: Dict[str, User] = get_users()

        with open(INPUT_FILE_NAME) as csvfile:
            reader: Any = csv.DictReader(csvfile)
            for count, row in enumerate(reader, start=1):
                if verbose:
                    print(f"{count} #{row['id']} {row['organisation_name']}")

                case = create_case(
                    row=row,
                    regions=regions,
                    sectors=sectors,
                    users=users,
                )

                regions: List[Region] = get_regions_from_row(row, regions)
                if regions:
                    case.region.add(regions)

                # if "Contact name" in row and row["Contact name"]:
                #     name_words = row["Contact name"].split()
                #     contact = Contact(
                #         case=case,
                #         first_name=name_words[0],
                #         last_name=" ".join(name_words[1:]),
                #         job_title=row["Job title"],
                #         detail=row["Contact detail"].split("\n")[0],
                #         notes=row["Contact detail"],
                #         created=created_time,
                #         created_by=auditor,
                #     )
                #     contact.save()
