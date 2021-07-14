"""
This command adds historic case data.
"""
import csv
from datetime import date, datetime
from functools import partial
from typing import Any, Callable, Dict, List, Union

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ...models import Case, Contact
from ....common.models import Region, Sector

INPUT_FILE_NAME = (
    "accessibility_monitoring_platform/apps/cases/management/commands/test_cases.csv"
)


def delete_existing_data(verbose: bool = False) -> None:
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


def get_boolean_from_row(row: Dict[str, str], column_name: str) -> Union[bool, None]:
    string = row.get(column_name, "")
    return string == "True" if string else None


def get_string_from_row(
    row: Dict[str, str], column_name: str, default: str = ""
) -> str:
    return row.get(column_name, default)


def get_integer_from_row(row: Dict[str, str], column_name: str = "id") -> int:
    id: str = row.get(column_name)
    return int(id)


def get_date_from_row(row: Dict[str, str], column_name: str) -> Union[date, None]:
    date_string: Union[str, None] = row.get(column_name)
    if date_string:
        yyyy, mm, dd = date_string.split("-")
        return date(int(yyyy), int(mm), int(dd))
    return None


def get_datetime_from_row(
    row: Dict[str, str], column_name: str
) -> Union[datetime, None]:
    datetime_string: Union[str, None] = row.get(column_name)
    if datetime_string:
        try:
            timestamp: datetime = datetime.strptime(
                datetime_string, "%Y-%m-%d %H:%M:%S.%f%z"
            )
        except ValueError:
            timestamp: datetime = datetime.strptime(
                datetime_string, "%Y-%m-%d %H:%M:%S%z"
            )
        return timestamp
    return None


def get_or_create_user_from_row(
    row: Dict[str, str], users: List[User], column_name: str
) -> Union[User, None]:
    user_email: Union[str, None] = row.get(column_name)
    if user_email and user_email not in users:
        name, _ = user_email.split("@")
        first_name, last_name = name.split(".")
        user: User = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=user_email,
            email=user_email,
        )
        users[user_email] = user
        return user
    return users.get(user_email) if user_email is not None else None


def get_or_create_sector_from_row(
    row: Dict[str, str], sectors: Dict[str, Sector]
) -> Union[Sector, None]:
    sector_name: Union[Sector, None] = row.get("sector")
    if sector_name and sector_name not in sectors:
        sector: Sector = Sector.objects.create(name=sector_name)
        sectors[sector_name] = sector
        return sector
    else:
        return sectors.get(sector_name)
    return None


def get_data_from_row(
    row: Dict[str, str],
    users: List[User],
    sectors: List[Sector],
    column_name: str,
    column_type: str = "string",
    default: Any = "",
) -> Union[str, bool, int, date, datetime, User, Sector]:
    if column_type == "string":
        return get_string_from_row(row=row, column_name=column_name, default=default)
    if column_type == "boolean":
        return get_boolean_from_row(row=row, column_name=column_name)
    if column_type == "integer":
        return get_integer_from_row(row=row, column_name=column_name)
    if column_type == "date":
        return get_date_from_row(row=row, column_name=column_name)
    if column_type == "datetime":
        return get_datetime_from_row(row=row, column_name=column_name)
    if column_type == "user":
        return get_or_create_user_from_row(
            row=row, users=users, column_name=column_name
        )
    if column_type == "sector":
        return get_or_create_sector_from_row(row=row, sectors=sectors)


def create_case(get_data: Callable) -> Case:
    return Case.objects.create(
        id=get_data(column_name="id", column_type="integer"),
        status=get_data(column_name="status", default="new-case"),
        created=get_data(column_name="created", column_type="datetime"),
        auditor=get_data(column_name="auditor", column_type="user"),
        test_type=get_data(column_name="test_type", default="simple"),
        home_page_url=get_data(column_name="home_page_url"),
        domain=get_data(column_name="domain"),
        application=get_data(column_name="application"),
        organisation_name=get_data(column_name="organisation_name"),
        website_type=get_data(column_name="website_type", default="public"),
        sector=get_data(column_name="sector", column_type="sector"),
        case_origin=get_data(column_name="case_origin", default="org"),
        zendesk_url=get_data(column_name="zendesk_url"),
        trello_url=get_data(column_name="trello_url"),
        notes=get_data(column_name="notes"),
        is_public_sector_body=get_data(
            column_name="is_public_sector_body", column_type="boolean"
        ),
        test_results_url=get_data(column_name="test_results_url"),
        test_status=get_data(column_name="test_status", default="not-started"),
        is_website_compliant=get_data(
            column_name="is_website_compliant", column_type="boolean"
        ),
        test_notes=get_data(column_name="test_notes"),
        report_draft_url=get_data(column_name="report_draft_url"),
        report_review_status=get_data(
            column_name="report_review_status", default="not-started"
        ),
        reviewer=get_data(column_name="reviewer", column_type="user"),
        report_approved_status=get_data(
            column_name="report_approved_status", default="not-started"
        ),
        reviewer_notes=get_data(column_name="reviewer_notes"),
        report_final_url=get_data(column_name="report_final_url"),
        report_sent_date=get_data(column_name="report_sent_date", column_type="date"),
        report_acknowledged_date=get_data(
            column_name="report_acknowledged_date", column_type="date"
        ),
        report_followup_week_12_due_date=get_data(
            column_name="report_followup_week_12_due_date", column_type="date"
        ),
        psb_progress_notes=get_data(column_name="psb_progress_notes"),
        report_followup_week_12_sent_date=get_data(
            column_name="report_followup_week_12_sent_date",
            column_type="date",
        ),
        is_website_retested=get_data(
            column_name="is_website_retested", column_type="boolean"
        ),
        is_disproportionate_claimed=get_data(
            column_name="is_disproportionate_claimed",
            column_type="boolean",
        ),
        disproportionate_notes=get_data(column_name="disproportionate_notes"),
        accessibility_statement_decison=get_data(
            column_name="accessibility_statement_decison",
            default="not-compliant",
        ),
        accessibility_statement_url=get_data(column_name="accessibility_statement_url"),
        accessibility_statement_notes=get_data(
            column_name="accessibility_statement_notes"
        ),
        compliance_decision=get_data(
            column_name="compliance_decision", default="unknown"
        ),
        compliance_decision_notes=get_data(column_name="compliance_decision_notes"),
        compliance_email_sent_date=get_data(
            column_name="compliance_email_sent_date",
            column_type="date",
        ),
        sent_to_enforcement_body_sent_date=get_data(
            column_name="sent_to_enforcement_body_sent_date",
            column_type="date",
        ),
        is_case_completed=get_data(
            column_name="is_case_completed", column_type="boolean"
        ),
        completed=get_data(column_name="completed", column_type="datetime"),
        is_archived=get_data(column_name="is_archived", column_type="boolean"),
    )


def get_or_create_regions_from_row(row: Dict[str, str], regions) -> List[Region]:
    region: Union[Region, None] = row.get("region", None)
    if region:
        region_names: List[str] = region.split(",")
        region_objects: List[Region] = []
        for region_name in region_names:
            if region_name in regions:
                region_objects.append(regions[region_name])
            else:
                new_region: Region = Region.objects.create(name=region_name)
                regions[region_name] = new_region
                region_objects.append(new_region)
        return region_objects
    return []


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

                get_data: Callable = partial(
                    get_data_from_row, row=row, users=users, sectors=sectors
                )
                case: Case = create_case(get_data)

                regions_for_case: List[Region] = get_or_create_regions_from_row(
                    row, regions
                )

                if regions_for_case:
                    case.region.add(*regions_for_case)

                if "contact_email" in row and row["contact_email"]:
                    contact: Contact = Contact(
                        case=case,
                        detail=get_data(column_name="contact_email"),
                        notes=get_data(column_name="contact_notes"),
                        created=get_data(column_name="created", column_type="datetime"),
                        created_by=get_data(column_name="auditor", column_type="user"),
                    )
                    contact.save()
