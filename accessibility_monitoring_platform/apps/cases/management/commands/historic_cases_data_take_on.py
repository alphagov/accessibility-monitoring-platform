"""
This command adds historic case data from a local copy
of the Simplified testing central spreadsheet as well
as an extract of data from the testing documents.
"""
import csv
from datetime import date, datetime
from functools import partial
from pathlib import Path
import pytz
import re
from typing import Any, Callable, Dict, List, Union

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from ...models import Case, Contact
from ....common.models import Sector, Region
from ....common.utils import extract_domain_from_url

CENTRAL_SPREADSHEET_FILE_NAME = Path.home() / "simplified_test_central_sheet.csv"
TEST_RESULTS_FILE_NAME = Path.home() / "historic_cases_test_results.csv"

# All columns in Simplified test central spreadsheet, with unused ones as comments:
CASE_NUMBER = " Case No."
CREATED_DATE = "Date"
ORGANISATION_NAME = "Website"
HOME_PAGE_URL = "URL of home page"
CONTACT_NAME = "Contact name"
JOB_TITLE = "Job title"
CONTACT_DETAIL = "Contact detail"
IS_IT_A_COMPLAINT = "Is it a complaint?"
AUDITOR = "Monitored by"
TEST_RESULTS_URL = "Link to monitor doc"
REPORT_FINAL_URL = "Link to report"
REPORT_SENT_DATE = "Report sent on"
REPORT_ACKNOWLEDGED_DATE = "Report acknowledged"
WEEK_12_FOLLOWEP_DATE = "Followup date - 12 week deadline"
PSB_PROGRESS_NOTES = "Summary of progress made / response from PSB"
IS_DISPROPORTIONATE_CLAIMBED = "Disproportionate Burden Claimed?"
DISPROPORTIONATE_NOTES = "Disproportionate Burden Notes"
ACCESSIBILITY_STATEMENT_DECISION = "Accessibility Statement Decision"
ACCESSIBILITY_STATEMENT_NOTES = "Notes on accessibility statement"
# Link to new saved screen shot of accessibility statement if not compliant
COMPLIANCE_DECISION = "Compliance Decision"
COMPLIANCE_DECISION_NOTES = "Compliance Decision Notes"
RETEST_DATE = "Retest date"  # Used to set is_website_retested flag
# Decision email sent?
GB_OR_NI = "GB or NI?"
SENT_TO_ENFORCEMENT_BODY_DATE = (
    "Date sent to enforcement body"  # Actually a month value
)
# Update from org once case was closed (if applicable)
# Enforcement body interested in case
# User Research
# Post audit survey
# METADATA
WEBSITE_TYPE = "Type of site"
SECTOR = "Sector"
# Scale
REGION = "Region"
CASE_ORIGIN = "Org or website list?"
# FOI checked


def delete_existing_data(verbose: bool = False) -> None:
    if verbose:
        print("Deleting all existing cases and contacts from database")

    Case.objects.all().delete()


def get_test_results_urls() -> Dict[int, str]:
    test_results_urls: Dict[int, str] = {}
    with open(TEST_RESULTS_FILE_NAME) as csvfile:
        reader: Any = csv.DictReader(csvfile)
        for row in reader:
            test_results_urls[int(row["Case number"])] = row["Home page URL"]
    return test_results_urls


def get_users() -> Dict[str, User]:
    return {user.first_name.lower(): user for user in User.objects.all()}


def get_regions() -> Dict[str, Region]:
    return {region.name.lower(): region for region in Region.objects.all()}


def get_sectors() -> Dict[str, Sector]:
    return {sector.name.lower(): sector for sector in Sector.objects.all()}


def print_row_message(row: Dict[str, str], message: str) -> None:
    print(f"#{row[CASE_NUMBER]} {row[ORGANISATION_NAME]}: {message}")


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
                print_row_message(
                    row, f"'{column_name}' has bad date string '{column_string}'"
                )
                return None
    return None


def get_month_from_row(row: Dict[str, str], column_name: str) -> Union[date, None]:
    """
    Given data such as "June 2020" return a date object for the first of that month.
    """
    column_string: Union[str, None] = row.get(column_name)
    if column_string and not column_string.startswith("n/a"):
        try:
            month, year = column_string.split()
            mm = datetime.strptime(month[:3], "%b").month
            return date(int(year), int(mm), int(1))
        except Exception:
            print_row_message(
                row, f"'{column_name}' has bad month string '{column_string}'"
            )
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
            print_row_message(row, f"'{column_name}' has bad user name '{user_name}'")
            return None
    return users.get(first_name_key) if user_name is not None else None


def get_or_create_sector_from_row(
    row: Dict[str, str], sectors: Dict[str, Sector], column_name: str
) -> Union[Sector, None]:
    sector_name: Union[str] = row.get(column_name, "").strip()
    if sector_name and sector_name.lower() not in sectors:
        sector: Sector = Sector.objects.create(name=sector_name)
        sectors[sector_name] = sector
        return sector
    else:
        return sectors.get(sector_name.lower())
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
    elif column_type == "boolean":
        return get_boolean_from_row(row=row, column_name=column_name)
    elif column_type == "integer":
        return get_integer_from_row(row=row, column_name=column_name)
    elif column_type == "date":
        return get_date_from_row(row=row, column_name=column_name)
    elif column_type == "datetime":
        return get_datetime_from_row(row=row, column_name=column_name)
    elif column_type == "user":
        return get_or_create_user_from_row(
            row=row, users=users, column_name=column_name
        )
    elif column_type == "sector":
        return get_or_create_sector_from_row(
            column_name=column_name, row=row, sectors=sectors
        )
    elif column_type == "month":
        return get_month_from_row(column_name=column_name, row=row)


def create_case(get_data: Callable, homepage_urls: Dict[int, str]) -> Case:
    case_number = get_data(column_name=CASE_NUMBER, column_type="integer")
    home_page_url = get_data(column_name=HOME_PAGE_URL)
    if not home_page_url:
        home_page_url = homepage_urls.get(case_number, "")
        # if home_page_url:
        #     print(
        #         f"#{case_number}: Got home page url from test results '{home_page_url}'"
        #     )
    is_complaint = get_data(column_name=IS_IT_A_COMPLAINT).strip() == "TRUE"
    compliance_decision_str = get_data(column_name=COMPLIANCE_DECISION)
    is_website_compliant = (
        "yes" if compliance_decision_str == "No further action" else "unknown"
    )
    report_sent_date = get_data(column_name=REPORT_SENT_DATE, column_type="date")
    report_review_status = "ready-to-review" if report_sent_date else "not-started"
    report_approved_status = "yes" if report_sent_date else "no"
    retested_website = get_data(column_name=RETEST_DATE, column_type="date")
    is_disproportionate_claimed = (
        "yes"
        if get_data(column_name=IS_DISPROPORTIONATE_CLAIMBED) == "Yes"
        else "unknown"
    )
    if compliance_decision_str:
        compliance_decision = (
            "inaction" if is_website_compliant else slugify(compliance_decision_str)
        )
    else:
        compliance_decision = "unknown"
    sent_to_enforcement_body = get_data(column_name=SENT_TO_ENFORCEMENT_BODY_DATE)
    case_completed = (
        "no-action"
        if sent_to_enforcement_body.lower() == "n/a - no need to send"
        else "no-decision"
    )

    return Case.objects.create(
        id=case_number,
        created=get_data(column_name=CREATED_DATE, column_type="datetime"),
        auditor=get_data(column_name=AUDITOR, column_type="user"),
        test_type="simple",
        home_page_url=home_page_url,
        domain=extract_domain_from_url(home_page_url),
        application="n/a",
        organisation_name=get_data(column_name=ORGANISATION_NAME),
        website_type=get_data(column_name=WEBSITE_TYPE),
        sector=get_data(column_name=SECTOR, column_type="sector"),
        is_complaint=is_complaint,
        zendesk_url="",
        trello_url="",
        notes="",
        is_public_sector_body="yes",
        test_results_url=get_data(column_name=TEST_RESULTS_URL),
        test_status="not-started",
        is_website_compliant=is_website_compliant,
        test_notes="",
        report_draft_url="",
        report_review_status=report_review_status,
        reviewer=None,
        report_approved_status=report_approved_status,
        reviewer_notes="",
        report_final_url=get_data(column_name=REPORT_FINAL_URL),
        report_sent_date=report_sent_date,
        report_acknowledged_date=get_data(
            column_name=REPORT_ACKNOWLEDGED_DATE, column_type="date"
        ),
        report_followup_week_12_due_date=get_data(
            column_name=WEEK_12_FOLLOWEP_DATE, column_type="date"
        ),
        report_followup_week_12_sent_date=None,
        psb_progress_notes=get_data(column_name=PSB_PROGRESS_NOTES),
        retested_website=retested_website,
        is_disproportionate_claimed=is_disproportionate_claimed,
        disproportionate_notes=get_data(column_name=DISPROPORTIONATE_NOTES),
        accessibility_statement_decison=slugify(
            get_data(column_name=ACCESSIBILITY_STATEMENT_DECISION)
        ),
        accessibility_statement_url="",
        accessibility_statement_notes=get_data(
            column_name=ACCESSIBILITY_STATEMENT_NOTES
        ),
        compliance_decision=compliance_decision,
        compliance_decision_notes=get_data(column_name=COMPLIANCE_DECISION_NOTES),
        compliance_email_sent_date=None,
        sent_to_enforcement_body_sent_date=get_data(
            column_name=SENT_TO_ENFORCEMENT_BODY_DATE, column_type="month"
        ),
        case_completed=case_completed,
        completed=None,
        is_archived=False,
    )


def get_or_create_regions_from_row(row: Dict[str, str], regions) -> List[Region]:
    region: Union[str, None] = row.get(REGION)
    gb_or_ni: Union[str, None] = row.get(GB_OR_NI)
    if region:
        region_names: List[str] = [
            region_name.strip() for region_name in region.split(",")
        ]
        if gb_or_ni and gb_or_ni == "NI":
            region_names.append("Northern Ireland")
        region_objects: List[Region] = []
        for region_name in region_names:
            region_name
            if region_name.lower() in regions:
                region_objects.append(regions[region_name.lower()])
            else:
                new_region: Region = Region.objects.create(name=region_name)
                regions[region_name.lower()] = new_region
                region_objects.append(new_region)
        return region_objects
    return []


def create_contact_from_row(get_data: Callable, case: Case) -> None:
    contact_name = get_data(column_name=CONTACT_NAME)
    job_title = get_data(column_name=JOB_TITLE)
    contact_detail = get_data(column_name=CONTACT_DETAIL)
    if contact_detail:
        contact: Contact = Contact(
            case=case,
            first_name="Historic",
            last_name=contact_name,
            job_title=job_title,
            detail=contact_detail,
            created=get_data(column_name=CREATED_DATE, column_type="datetime"),
            created_by=get_data(column_name=AUDITOR, column_type="user"),
        )
        contact.save()


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
        parser.add_argument(
            "--contacts",
            action="store_true",
            dest="contacts",
            default=False,
            help="Create contacts",
        )

    def handle(self, *args, **options):
        """
        Reach through historic Case data csv and create entries on database.

        Delete existing Case and Contact data if --initial option is passed.
        """
        verbose: bool = options["verbose"]
        initial: bool = options["initial"]
        create_contacts: bool = options["contacts"]

        if initial:
            delete_existing_data(verbose)

        homepage_urls: Dict[int, str] = get_test_results_urls()
        regions: Dict[str, Region] = get_regions()
        sectors: Dict[str, Sector] = get_sectors()
        users: Dict[str, User] = get_users()

        with open(CENTRAL_SPREADSHEET_FILE_NAME) as csvfile:
            reader: Any = csv.DictReader(csvfile)
            for count, row in enumerate(reader, start=1):
                if not row[CREATED_DATE]:
                    break

                if verbose:
                    print(f"{count} #{row[CASE_NUMBER]} {row['Website']}")

                get_data: Callable = partial(
                    get_data_from_row, row=row, users=users, sectors=sectors
                )
                case: Case = create_case(get_data, homepage_urls=homepage_urls)

                regions_for_case: List[Region] = get_or_create_regions_from_row(
                    row, regions
                )

                if regions_for_case:
                    case.region.add(*regions_for_case)

                if create_contacts:
                    create_contact_from_row(get_data, case)
