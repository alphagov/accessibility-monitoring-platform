"""
This command adds historic case data.
"""
import csv
from datetime import datetime
from functools import partial
from typing import Any, Callable, Dict, Optional, Union

from django.core.management.base import BaseCommand
from django.db import models
from django.db.models.fields.reverse_related import ManyToOneRel

from ...models import ReportTemplate

INPUT_FILE_NAME = (
    "accessibility_monitoring_platform/apps/reports/management/commands/report_templates.csv"
)


def delete_existing_data(verbose: bool = False) -> None:
    if verbose:
        print("Deleting all existing report templates from database")
    ReportTemplate.objects.all().delete()


def get_string_from_row(
    row: Dict[str, str], column_name: str, default: str = ""
) -> str:
    return row.get(column_name, default)


def get_integer_from_row(row: Dict[str, str], column_name: str = "id") -> int:
    id_str: Optional[str] = row.get(column_name)
    return int(id_str)  # type: ignore


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


def get_data_from_row(
    row: Dict[str, str],
    field: models.Field,
) -> Union[str, int, datetime, None]:
    if isinstance(field, (models.CharField, models.TextField)):
        return get_string_from_row(
            row=row, column_name=field.name, default=field.default
        )
    if isinstance(field, models.IntegerField or isinstance(field, models.AutoField)):
        return get_integer_from_row(row=row, column_name=field.name)
    if isinstance(field, models.DateTimeField):
        return get_datetime_from_row(row=row, column_name=field.name)


def create_report_template(get_data: Callable) -> ReportTemplate:
    fields = ReportTemplate._meta.get_fields()  # pylint: disable=protected-access
    kwargs = {
        field.name: get_data(field=field)
        for field in fields
        if not isinstance(field, ManyToOneRel)
    }
    return ReportTemplate.objects.create(**kwargs)


class Command(BaseCommand):
    """
    Command to load ReportTemplate data from csv
    """

    help = "Add ReportTemplate data to database."

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
        Read through ReportTemplate data csv and create entries on database.

        Delete existing ReportTemplate data if --initial option is passed.
        """
        verbose: bool = options["verbose"]
        initial: bool = options["initial"]

        if initial:
            delete_existing_data(verbose)

        with open(INPUT_FILE_NAME) as csvfile:
            reader: Any = csv.DictReader(csvfile)
            for count, row in enumerate(reader, start=1):
                if verbose:
                    print(f"{count} #{row['id']} {row['name']}")

                get_data: Callable = partial(
                    get_data_from_row, row=row,
                )
                create_report_template(get_data)
