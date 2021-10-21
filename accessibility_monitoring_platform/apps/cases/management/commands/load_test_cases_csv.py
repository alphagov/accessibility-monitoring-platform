"""
This command adds historic case data.
"""
import csv
from datetime import date, datetime
from functools import partial
from typing import Any, Callable, Dict, Optional, Union

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import models
from django.db.models.fields.reverse_related import ManyToOneRel

from ...models import Case, Contact
from ....common.models import Sector

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
    id_str: Optional[str] = row.get(column_name)
    return int(id_str)  # type: ignore


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
    row: Dict[str, str], users: Dict[str, User], column_name: str
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
    sector_name: Union[str, None] = row.get("sector")
    if sector_name:
        if sector_name not in sectors:
            sector: Sector = Sector.objects.create(name=sector_name)
            sectors[sector_name] = sector
            return sector
        else:
            return sectors.get(sector_name)
    return None


def get_data_from_row(
    row: Dict[str, str],
    users: Dict[str, User],
    sectors: Dict[str, Sector],
    field: models.Field,
) -> Union[str, bool, int, date, datetime, User, Sector, None]:
    if isinstance(field, (models.CharField, models.TextField)):
        return get_string_from_row(
            row=row, column_name=field.name, default=field.default
        )
    if isinstance(field, models.BooleanField):
        return get_boolean_from_row(row=row, column_name=field.name)
    if isinstance(field, models.IntegerField or isinstance(field, models.AutoField)):
        return get_integer_from_row(row=row, column_name=field.name)
    if isinstance(field, models.DateTimeField):
        return get_datetime_from_row(row=row, column_name=field.name)
    if isinstance(field, models.DateField):
        return get_date_from_row(row=row, column_name=field.name)
    if isinstance(field, models.ForeignKey) and field.related_model == User:
        return get_or_create_user_from_row(row=row, users=users, column_name=field.name)
    if isinstance(field, models.ForeignKey) and field.related_model == Sector:
        return get_or_create_sector_from_row(row=row, sectors=sectors)


def create_case(get_data: Callable) -> Case:
    fields = Case._meta.get_fields()
    kwargs = {
        field.name: get_data(field=field)
        for field in fields
        if not isinstance(field, ManyToOneRel)
    }
    return Case.objects.create(**kwargs)


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

                if "contact_email" in row and row["contact_email"]:
                    contact: Contact = Contact(
                        case=case,
                        email=get_string_from_row(row=row, column_name="contact_email"),
                        notes=get_string_from_row(row=row, column_name="contact_notes"),
                        created=get_datetime_from_row(row=row, column_name="created"),
                        created_by=get_or_create_user_from_row(
                            row=row, users=users, column_name="auditor"
                        ),
                    )
                    contact.save()
