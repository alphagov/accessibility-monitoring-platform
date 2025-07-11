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
from ..notifications.models import Task
from .models import Contact, DetailedCase, DetailedCaseHistory, DetailedEventHistory


def record_detailed_model_create_event(
    user: User, model_object: models.Model, detailed_case: DetailedCase
) -> None:
    """Record model create event"""
    model_object_fields = copy.copy(vars(model_object))
    del model_object_fields["_state"]
    DetailedEventHistory.objects.create(
        detailed_case=detailed_case,
        created_by=user,
        parent=model_object,
        event_type=DetailedEventHistory.Type.CREATE,
        difference=json.dumps(model_object_fields, default=str),
    )


def record_detailed_model_update_event(
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
        DetailedEventHistory.objects.create(
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


def add_note_to_history(
    detailed_case: DetailedCase, created: datetime, created_by: User, note: str
) -> None:
    detailed_case_history: DetailedCaseHistory = DetailedCaseHistory.objects.create(
        detailed_case=detailed_case,
        event_type=DetailedCaseHistory.EventType.NOTE,
        value=note,
        created_by=created_by,
    )
    detailed_case_history.created = created
    detailed_case_history.save()


def create_detailed_case_from_dict(
    row: dict[str, Any], default_user: User, auditors: dict[str, User]
) -> None:
    original_record_number: str = row["Record "]
    first_contact_date: str = row["First Contact Date"]  # dd/mm/yyyy
    if first_contact_date:
        created: datetime = get_datetime_from_string(first_contact_date)
    else:
        created: datetime = datetime.now().astimezone(timezone.utc)
    last_date: str = row["Date decision email sent"]  # dd/mm/yyyy
    if len(last_date) > 4:
        updated: datetime = get_datetime_from_string(last_date)
    else:
        updated: datetime = created
    auditor: User = auditors.get(row["Auditor"], default_user)
    url: str = row["URL"] if row["URL"].startswith("http") else ""
    qa_auditors: str = row["Report checked by"]
    if " " in qa_auditors:
        qa_auditor: User = auditors.get(qa_auditors.split(" ")[0], default_user)
    else:
        qa_auditor: User = auditors.get(qa_auditors, default_user)
    report_sent_on: str = row["Report sent on"]  # dd/mm/yyyy
    report_sent_date: None | datetime = (
        get_datetime_from_string(report_sent_on) if len(report_sent_on) > 4 else None
    )

    detailed_case: DetailedCase = DetailedCase.objects.create(
        test_type=DetailedCase.TestType.DETAILED,
        created_by_id=default_user.id,
        updated=updated,
        auditor_id=auditor.id,
        home_page_url=url,
        domain=extract_domain_from_url(url=url),
        organisation_name=row["Organisation name"],
        website_name=row["Website"],
        enforcement_body=row["Enforcement body"].lower(),
        is_complaint=row["Is it a complaint?"].lower(),
        notes=row["Summary of progress made / response from PSB"],
        service_type=row["Type"].lower(),
        monitor_doc_url=row["Link to monitor doc"],
        public_report_url=row["Public link to report PDF"],
        reviewer=qa_auditor,
        report_sent_date=report_sent_date,
    )
    detailed_case.created = created
    detailed_case.save()
    if row["Related case notes (if applicable)"]:
        add_note_to_history(
            detailed_case=detailed_case,
            created=updated,
            created_by=auditor,
            note=f'Related case notes:\n\n{row["Related case notes (if applicable)"]}',
        )
    add_note_to_history(
        detailed_case=detailed_case,
        created=updated,
        created_by=auditor,
        note=f"Original record number is {original_record_number}",
    )
    if " " in qa_auditors:
        add_note_to_history(
            detailed_case=detailed_case,
            created=updated,
            created_by=auditor,
            note=f"All QA auditors: {qa_auditors}",
        )
    detailed_case_status_history: DetailedCaseHistory = (
        DetailedCaseHistory.objects.create(
            detailed_case_id=detailed_case.id,
            event_type=DetailedCaseHistory.EventType.STATUS,
            value="Initial",
            created_by=auditor,
        )
    )
    detailed_case_status_history.created = updated
    detailed_case_status_history.save()
    contact: Contact = Contact.objects.create(
        detailed_case=detailed_case,
        name=row["Contact name"],
        job_title=row["Job title"],
        contact_point=row["Contact detail"],
        created_by=auditor,
    )
    contact.created = updated
    contact.save()


def import_detailed_cases_csv(csv_data: str) -> None:
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

    Contact.objects.all().delete()
    DetailedEventHistory.objects.all().delete()
    DetailedCaseHistory.objects.all().delete()
    for detailed_case in DetailedCase.objects.all():
        Task.objects.filter(base_case=detailed_case).delete()
    DetailedCase.objects.all().delete()

    reader: Any = csv.DictReader(io.StringIO(csv_data))
    for row in reader:
        if row["Enforcement body"] == "":
            continue
        create_detailed_case_from_dict(
            row=row, default_user=default_user, auditors=auditors
        )
