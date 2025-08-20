"""
Utils for mobile Case app
"""

import copy
import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

from django.contrib.auth.models import User
from django.db import models

from ..common.utils import diff_model_fields, extract_domain_from_url
from .models import EventHistory, MobileCase, MobileCaseHistory


def record_mobile_model_create_event(
    user: User, model_object: models.Model, mobile_case: MobileCase
) -> None:
    """Record model create event"""
    model_object_fields = copy.copy(vars(model_object))
    del model_object_fields["_state"]
    EventHistory.objects.create(
        mobile_case=mobile_case,
        created_by=user,
        parent=model_object,
        event_type=EventHistory.Type.CREATE,
        difference=json.dumps(model_object_fields, default=str),
    )


def record_mobile_model_update_event(
    user: User, model_object: models.Model, mobile_case: MobileCase
) -> None:
    """Record model update event"""
    previous_object = model_object.__class__.objects.get(pk=model_object.id)
    previous_object_fields = copy.copy(vars(previous_object))
    del previous_object_fields["_state"]
    model_object_fields = copy.copy(vars(model_object))
    del model_object_fields["_state"]
    diff_fields: dict[str, Any] = diff_model_fields(
        old_fields=previous_object_fields, new_fields=model_object_fields
    )
    if diff_fields:
        EventHistory.objects.create(
            mobile_case=mobile_case,
            created_by=user,
            parent=model_object,
            difference=json.dumps(diff_fields, default=str),
        )


def get_datetime_from_string(date: str) -> datetime | None:
    if len(date) < 5:
        return None
    if date[0].isdigit():
        # dd/mm/yyyy
        day, month, year = date.split("/")
        day: int = int(day)
        month: int = int(month)
        year: int = int(year)
        if year < 100:
            year += 2000
        return datetime(year, month, day, tzinfo=timezone.utc)
    # mmm yyyy
    return datetime.strptime(f"1 {date}", "%d %b %Y").replace(tzinfo=timezone.utc)


def validate_url(url: str) -> str:
    if url.startswith("http"):
        return url
    return ""


def add_note_to_history(
    mobile_case: MobileCase, created: datetime, created_by: User, note: str
) -> None:
    mobile_case_history: MobileCaseHistory = MobileCaseHistory.objects.create(
        mobile_case=mobile_case,
        event_type=MobileCaseHistory.EventType.NOTE,
        value=note,
        created_by=created_by,
    )
    mobile_case_history.created = created
    mobile_case_history.save()
    record_mobile_model_create_event(
        user=created_by, model_object=mobile_case_history, mobile_case=mobile_case
    )


def create_mobile_case_from_dict(
    row: dict[str, Any], default_user: User, auditors: dict[str, User]
) -> None:
    """User dictionary date (from csv) to create mobile Case"""
    case_number: int = int(row["Record "][1:])
    app_os: str = row["Type"].lower()
    created: datetime = get_datetime_from_string(row["First contact date"])
    last_date: str = get_datetime_from_string(row["Date decision email sent"])
    if last_date is not None:
        updated: datetime = last_date
    else:
        updated: datetime = created
    auditor: User = auditors.get(row["Auditor"], default_user)
    url: str = validate_url(row["URL"])
    enforcement_body: str = row["Enforcement body"].lower()
    is_complaint: str = row["Is it a complaint?"].lower()
    mobile_case: MobileCase = MobileCase.objects.create(
        test_type=MobileCase.TestType.MOBILE,
        created_by_id=default_user.id,
        updated=updated,
        auditor_id=auditor.id,
        app_name=row["App name"],
        app_store_url=url,
        domain=extract_domain_from_url(url),
        app_os=app_os,
        enforcement_body=enforcement_body,
        is_complaint=is_complaint,
        case_folder_url=row["Link to case folder"],
        initial_test_start_date=get_datetime_from_string(row["Test start date"]),
        initial_test_end_date=get_datetime_from_string(row["Test end date"]),
    )
    mobile_case.created = created
    mobile_case.case_number = case_number
    mobile_case.case_identifier = f"#M-{case_number}"
    mobile_case.save()
    for column_name in [
        "Summary of progress made / response from PSB",
    ]:
        if row[column_name]:
            add_note_to_history(
                mobile_case=mobile_case,
                created=updated,
                created_by=auditor,
                note=f"Legacy {column_name}:\n\n{row[column_name]}",
            )


def import_mobile_cases_csv(csv_data: str) -> None:
    default_user = User.objects.filter(first_name="Paul").first()
    if default_user is None:
        return
    try:
        auditors: dict[str, User] = {
            first_name: User.objects.get(first_name=first_name)
            for first_name in ["Andrew", "Katherine", "Kelly"]
        }
    except User.DoesNotExist:  # Automated tests
        auditors = {}

    EventHistory.objects.all().delete()
    MobileCaseHistory.objects.all().delete()
    MobileCase.objects.all().delete()

    reader: Any = csv.DictReader(io.StringIO(csv_data))
    for row in reader:
        if row["Enforcement body"] == "":
            continue
        create_mobile_case_from_dict(
            row=row, default_user=default_user, auditors=auditors
        )
