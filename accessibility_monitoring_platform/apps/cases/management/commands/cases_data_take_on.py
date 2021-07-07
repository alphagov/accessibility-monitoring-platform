"""
This command adds historic case data.
"""
import csv
from datetime import date, datetime
from functools import partial
from os.path import expanduser
import pytz
import re
from typing import Any, Callable, Dict, List, Union

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from ...models import Case, Contact
from ....common.models import Sector, Region
from ....common.utils import extract_domain_from_url

HOME_PATH = expanduser("~")
INPUT_FILE_NAME = f"{HOME_PATH}/simplified_test_central_sheet_2021-07-07.csv"


def delete_existing_data(verbose: bool = False) -> None:
    if verbose:
        print("Deleting all existing cases and contacts from database")

    Case.objects.all().delete()


def get_users() -> Dict[str, User]:
    return {user.first_name.lower(): user for user in User.objects.all()}


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
    column_string: Union[str, None] = row.get(column_name)
    if column_string:
        date_string = re.search(r"\d+/\d+/\d+", column_string)
        if date_string:
            try:
                dd, mm, yyyy = date_string.group().split("/")
                return date(int(yyyy), int(mm), int(dd))
            except Exception:
                return None
    return None


def get_datetime_from_row(
    row: Dict[str, str], column_name: str
) -> Union[datetime, None]:
    date: Union[date, None] = get_date_from_row(row, column_name)
    if date:
        return datetime(date.year, date.month, date.day, tzinfo=pytz.UTC)
    return None


def get_or_create_user_from_row(
    row: Dict[str, str], users: List[User], column_name: str
) -> Union[User, None]:
    user_name: Union[str, None] = row.get(column_name)
    first_name_key = re.split(r" |\.", user_name.strip())[0].lower()
    if first_name_key and first_name_key not in users:
        user_email = f"{user_name.replace(' ', '.')}@digital.cabinet-office.gov.uk"
        try:
            first_name, last_name = user_name.strip().split(" ")
            user: User = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                username=user_email,
                email=user_email,
            )
            users[first_name_key] = user
            return user
        except Exception:
            return None
    return users.get(first_name_key) if user_name is not None else None


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


def get_status_from_row(row: Dict[str, str]) -> str:
    if row["Date sent to enforcement body"].lower() == "n/a - no need to send":
        return "complete"
    if row["Date sent to enforcement body"]:
        return "escalated"
    if row["Report sent on"] and not row["Report acknowledged"]:
        return "awaiting-response"
    if row["Followup date - 12 week deadline"] and not row["Summary of progress made / response from PSB"]:
        return "12w-due"
    return "new-case"
    # Unused statuses:
    #  "test-in-progress"
    #  "report-in-progress"
    #  "12w-sent"
    #  "archived"
    #  "not-a-psb"


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
    if column_type == "status":
        return get_status_from_row(row=row)


def create_case(get_data: Callable) -> Case:
    home_page_url = get_data(column_name="URL of home page")
    compliance_decision_str = get_data(column_name="Compliance Decision")
    is_website_compliant = compliance_decision_str == "No further action"
    report_review_status = "ready-to-review" if get_data(column_name="Report sent on") else "not-started"
    report_approved_status = "yes" if get_data(column_name="Report sent on") else "no"
    is_website_retested = get_data(column_name="Retest date") != ""
    is_disproportionate_claimed = get_data(column_name="Disproportionate Burden Claimed?") == "Yes"
    if compliance_decision_str:
        compliance_decision = "inaction" if is_website_compliant else slugify(compliance_decision_str)
    else:
        compliance_decision = "unknown"

    return Case.objects.create(
        id=get_data(column_name=" Case No.", column_type="integer"),
        status=get_data(column_name="status", column_type="status"),
        created=get_data(column_name="Date", column_type="datetime"),
        auditor=get_data(column_name="Monitored by", column_type="user"),
        test_type="simple",
        home_page_url=home_page_url,
        domain=extract_domain_from_url(home_page_url),
        application="n/a",
        organisation_name=get_data(column_name="Website"),
        website_type=get_data(column_name="Type of site"),
        sector=get_data(column_name="Sector", column_type="sector"),
        case_origin=get_data(column_name="Org or website list?", default="list").lower(),
        zendesk_url="",
        trello_url="",
        notes="",
        is_public_sector_body=True,
        test_results_url=get_data(column_name="Link to monitor doc"),
        test_status="not-started",
        is_website_compliant=is_website_compliant,
        test_notes="",
        report_draft_url="",
        report_review_status=report_review_status,
        reviewer=None,
        report_approved_status=report_approved_status,
        reviewer_notes="",
        report_final_url=get_data(column_name="Link to report"),
        report_sent_date=get_data(column_name="Report sent on", column_type="date"),
        report_acknowledged_date=get_data(
            column_name="Report acknowledged", column_type="date"
        ),
        week_12_followup_date=get_data(
            column_name="Followup date - 12 week deadline", column_type="date"
        ),
        psb_progress_notes=get_data(column_name="Summary of progress made / response from PSB"),
        week_12_followup_email_sent_date=None,
        week_12_followup_email_acknowledgement_date=None,
        is_website_retested=is_website_retested,
        is_disproportionate_claimed=is_disproportionate_claimed,
        disproportionate_notes=get_data(column_name="Disproportionate Burden Notes"),
        accessibility_statement_decison=slugify(get_data(column_name="Accessibility Statement Decision")),
        accessibility_statement_url="",
        accessibility_statement_notes=get_data(column_name="Notes on accessibility statement"),
        compliance_decision=compliance_decision,
        compliance_decision_notes=get_data(column_name="Compliance Decision Notes"),
        compliance_email_sent_date=None,
        #  Todo:
        sent_to_enforcement_body_sent_date=None,
        is_case_completed=False,
        completed=None,
        is_archived=False,
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
            delete_existing_data(verbose)

        regions: Dict[str, Region] = get_regions()
        sectors: Dict[str, Sector] = get_sectors()
        users: Dict[str, User] = get_users()

        with open(INPUT_FILE_NAME) as csvfile:
            reader: Any = csv.DictReader(csvfile)
            for count, row in enumerate(reader, start=1):
                if not row["Date"]:
                    break

                if verbose:
                    print(f"{count} #{row[' Case No.']} {row['Website']}")

                get_data: Callable = partial(
                    get_data_from_row, row=row, users=users, sectors=sectors
                )
                case: Case = create_case(get_data)

                regions_for_case: List[Region] = get_or_create_regions_from_row(
                    row, regions
                )

                if regions_for_case:
                    case.region.add(*regions_for_case)

                # if "contact_email" in row and row["contact_email"]:
                #     contact: Contact = Contact(
                #         case=case,
                #         detail=get_data(column_name="contact_email"),
                #         notes=get_data(column_name="contact_notes"),
                #         created=get_data(column_name="created", column_type="datetime"),
                #         created_by=get_data(column_name="auditor", column_type="user"),
                #     )
                #     contact.save()
