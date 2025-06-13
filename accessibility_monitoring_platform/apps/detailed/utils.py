"""
Utils for detailed Case app
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
from .models import DetailedCase, DetailedCaseHistory, EventHistory


def record_model_create_event(
    user: User, model_object: models.Model, detailed_case: DetailedCase
) -> None:
    """Record model create event"""
    model_object_fields = copy.copy(vars(model_object))
    del model_object_fields["_state"]
    EventHistory.objects.create(
        detailed_case=detailed_case,
        created_by=user,
        parent=model_object,
        event_type=EventHistory.Type.CREATE,
        difference=json.dumps(model_object_fields, default=str),
    )


def record_model_update_event(
    user: User, model_object: models.Model, detailed_case: DetailedCase
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
            detailed_case=detailed_case,
            created_by=user,
            parent=model_object,
            difference=json.dumps(diff_fields, default=str),
        )


def add_to_detailed_case_history(
    detailed_case: DetailedCase,
    user: User,
    value: str,
    event_type: DetailedCaseHistory.EventType = DetailedCaseHistory.EventType.NOTE,
) -> None:
    """Add latest change of DetailedCase.status to history"""
    DetailedCaseHistory.objects.create(
        detailed_case=detailed_case,
        event_type=event_type,
        created_by=user,
        value=value,
    )


def get_datetime_from_string(date: str) -> datetime:
    day, month, year = date.split("/")
    day: int = int(day)
    month: int = int(month)
    year: int = int(year)
    if year < 100:
        year += 2000
    return datetime(year, month, day, tzinfo=timezone.utc)


def create_detailed_case_from_dict(
    row: dict[str, Any], default_user: User, auditors: dict[str, User]
) -> None:
    case_number: int = int(row["Record "][1:])
    first_contact_date: str = row["First Contact Date"]  # dd/mm/yyyy
    created: datetime = get_datetime_from_string(first_contact_date)
    last_date: str = row["Date decision email sent"]  # dd/mm/yyyy
    if len(last_date) > 4:
        updated: datetime = get_datetime_from_string(last_date)
    else:
        updated: datetime = created
    auditor: User = auditors.get(row["Auditor"], default_user)
    url: str = row["URL"]
    enforcement_body: str = row["Enforcement body"].lower()
    is_complaint: str = row["Is it a complaint?"].lower()

    detailed_case: DetailedCase = DetailedCase.objects.create(
        test_type=DetailedCase.TestType.DETAILED,
        case_number=case_number,
        created_by_id=default_user.id,
        created=created,
        updated=updated,
        auditor_id=auditor.id,
        home_page_url=url,
        domain=extract_domain_from_url(url=url),
        organisation_name=row["Website"],
        enforcement_body=enforcement_body,
        is_complaint=is_complaint,
        notes=row["Summary of progress made / response from PSB"],
    )
    detailed_case_status_history: DetailedCaseHistory = (
        DetailedCaseHistory.objects.create(
            detailed_case_id=detailed_case.id,
            event_type="status",
            value="Initial",
            created_by_id=auditor.id,
        )
    )
    detailed_case_status_history.created = updated
    detailed_case_status_history.save()


def import_detailed_cases_csv(csv_data: str) -> None:
    default_user = User.objects.filter(first_name="Paul").first()
    try:
        auditors: dict[str, User] = {
            first_name: User.objects.get(first_name=first_name)
            for first_name in ["Andrew", "Katherine", "Kelly"]
        }
    except User.DoesNotExist:  # Automated tests
        auditors = {}

    EventHistory.objects.all().delete()
    DetailedCaseHistory.objects.all().delete()
    DetailedCase.objects.all().delete()

    reader: Any = csv.DictReader(io.StringIO(csv_data))
    for row in reader:
        if row["Enforcement body"] == "":
            continue
        create_detailed_case_from_dict(
            row=row, default_user=default_user, auditors=auditors
        )


def import_mobile_cases_csv(data: str) -> None:
    pass
