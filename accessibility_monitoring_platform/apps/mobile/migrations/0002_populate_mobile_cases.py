# Generated by Django 5.2.1 on 2025-05-20 07:53

import csv
import re
from datetime import datetime, timezone
from typing import Match

from django.db import migrations

from ..utils import create_mobile_case_from_dict

INPUT_FILE_NAME = "../mobile_cases.csv"


def get_datetime_from_string(date: str) -> datetime:
    day, month, year = date.split("/")
    day: int = int(day)
    month: int = int(month)
    year: int = int(year)
    if year < 100:
        year += 2000
    return datetime(year, month, day, tzinfo=timezone.utc)


def extract_domain_from_url(url: str) -> str:
    """Extract and return domain string from url string"""
    if url.startswith("https://"):
        url = url[8:]
    elif url.startswith("http://"):
        url = url[7:]
    domain_match: Match[str] | None = re.search("([A-Za-z_0-9.-]+).*", url)
    return domain_match.group(1) if domain_match else ""


def populate_mobile_cases(apps, schema_editor):  # pylint: disable=unused-argument
    User = apps.get_model("auth", "User")
    try:
        default_user = User.objects.get(first_name="Paul")
        auditors: dict[str, User] = {
            first_name: User.objects.get(first_name=first_name)
            for first_name in ["Andrew", "Katherine", "Kelly"]
        }
    except User.DoesNotExist:  # Automated tests
        return
    EventHistory = apps.get_model("mobile", "EventHistory")
    EventHistory.objects.all().delete()
    MobileCase = apps.get_model("mobile", "MobileCase")
    MobileCase.objects.all().delete()
    try:
        with open(INPUT_FILE_NAME) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["Enforcement body"] == "":
                    continue
                create_mobile_case_from_dict(
                    row=row, default_user=default_user, auditors=auditors
                )
    except FileNotFoundError:
        pass


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    EventHistory = apps.get_model("mobile", "EventHistory")
    EventHistory.objects.all().delete()
    MobileCase = apps.get_model("mobile", "MobileCase")
    MobileCase.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("mobile", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(populate_mobile_cases, reverse_code=reverse_code),
    ]
