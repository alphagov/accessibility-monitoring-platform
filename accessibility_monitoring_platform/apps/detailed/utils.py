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

from ..common.models import Boolean
from ..common.utils import diff_model_fields, extract_domain_from_url
from ..notifications.models import Task
from .models import (
    Contact,
    DetailedCase,
    DetailedCaseHistory,
    DetailedEventHistory,
    ZendeskTicket,
)

ZENDESK_URL_PREFIX: str = "https://govuk.zendesk.com/agent/tickets/"
MAP_STATEMENT_COMPLIANCE: dict[str, str] = {
    "not compliant": DetailedCase.StatementCompliance.NOT_COMPLIANT,
    "": DetailedCase.StatementCompliance.UNKNOWN,
    "other": DetailedCase.StatementCompliance.UNKNOWN,
    "compliant": DetailedCase.StatementCompliance.COMPLIANT,
}
MAP_ENFORCEMENT_RECOMMENDATION: dict[str, str] = {
    "No further action": DetailedCase.RecommendationForEnforcement.NO_FURTHER_ACTION,
    "For enforcement consideration": DetailedCase.RecommendationForEnforcement.OTHER,
    "": DetailedCase.RecommendationForEnforcement.UNKNOWN,
}
MAP_ENFORCEMENT_BODY_CLOSED_CASE: dict[str, str] = {
    "No": DetailedCase.EnforcementBodyClosedCase.YES,
    "Yes": DetailedCase.EnforcementBodyClosedCase.IN_PROGRESS,
    "": DetailedCase.EnforcementBodyClosedCase.NO,
}


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


def get_datetime_from_string(date: str) -> None | datetime:
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


def validate_url(url: str) -> str:
    if url.startswith("http"):
        return url
    return ""


def create_detailed_case_from_dict(
    row: dict[str, Any], default_user: User, auditors: dict[str, User]
) -> None:
    original_record_number: str = row["Record "]
    first_contact_date: str = get_datetime_from_string(
        row["First Contact Date"]
    )  # dd/mm/yyyy
    if first_contact_date:
        created: datetime = first_contact_date
    else:
        created: datetime = datetime.now().astimezone(timezone.utc)
    last_date: str = row["Date decision email sent"]  # dd/mm/yyyy
    last_updated: datetime = get_datetime_from_string(last_date)
    if last_updated is None:
        last_updated: datetime = created
    auditor: User = auditors.get(row["Auditor"], default_user)
    url: str = validate_url(row["URL"])
    qa_auditors: str = row["Report checked by"]
    if " " in qa_auditors:
        qa_auditor: User = auditors.get(qa_auditors.split(" ")[0], default_user)
    else:
        qa_auditor: User = auditors.get(qa_auditors, default_user)
    feedback_survey_sent: str = row["Feedback survey sent"]
    is_feedback_survey_sent: Boolean = (
        Boolean.YES if feedback_survey_sent == "Yes" else Boolean.NO
    )

    detailed_case: DetailedCase = DetailedCase.objects.create(
        test_type=DetailedCase.TestType.DETAILED,
        created_by_id=default_user.id,
        updated=last_updated,
        auditor_id=auditor.id,
        home_page_url=url,
        domain=extract_domain_from_url(url=url),
        organisation_name=row["Organisation name"],
        website_name=row["Website"],
        enforcement_body=row["Enforcement body"].lower(),
        is_complaint=row["Is it a complaint?"].lower(),
        notes=row["Summary of progress made / response from PSB"],
        service_type=row["Type"].lower(),
        monitor_doc_url=validate_url(row["Link to monitor doc"]),
        public_report_url=validate_url(row["Public link to report PDF"]),
        reviewer=qa_auditor,
        report_sent_date=get_datetime_from_string(row["Report sent on"]),
        report_acknowledged_date=get_datetime_from_string(row["Report acknowledged"]),
        twelve_week_deadline_date=get_datetime_from_string(
            row["Followup date - 12 week deadline"]
        ),
        retest_statement_compliance_state=MAP_STATEMENT_COMPLIANCE[
            row["Accessibility Statement Decision"].lower()
        ],
        retest_statement_backup_url=validate_url(
            row["Link to new copy of accessibility statement if not compliant"]
        ),
        recommendation_for_enforcement=MAP_ENFORCEMENT_RECOMMENDATION[
            row["Enforcement Recommendation"]
        ],
        retest_date=get_datetime_from_string(row["Retest date"]),
        case_close_decision_sent_date=get_datetime_from_string(
            row["Date decision email sent"]
        ),
        enforcement_body_sent_date=get_datetime_from_string(
            row["Date sent to enforcement body"]
        ),
        enforcement_body_closed_case_state=MAP_ENFORCEMENT_BODY_CLOSED_CASE[
            row["Active case with enforcement body?"]
        ],
        is_feedback_survey_sent=is_feedback_survey_sent,
    )
    detailed_case.created = created
    detailed_case.save()

    detailed_case_status_history: DetailedCaseHistory = (
        DetailedCaseHistory.objects.create(
            detailed_case_id=detailed_case.id,
            event_type=DetailedCaseHistory.EventType.STATUS,
            value="Initial",
            created_by=auditor,
        )
    )
    detailed_case_status_history.created = last_updated
    detailed_case_status_history.save()

    add_note_to_history(
        detailed_case=detailed_case,
        created=last_updated,
        created_by=auditor,
        note=f"Original record number is {original_record_number}",
    )
    if " " in qa_auditors:
        add_note_to_history(
            detailed_case=detailed_case,
            created=last_updated,
            created_by=auditor,
            note=f"All QA auditors: {qa_auditors}",
        )

    for column_name in [
        "Related case notes (if applicable)",
        "Summary of progress made / response from PSB",
        "Disproportionate Burden Notes",
        "Notes on accessibility statement",
        "Enforcement Recommendation Notes",
    ]:
        if row[column_name]:
            add_note_to_history(
                detailed_case=detailed_case,
                created=last_updated,
                created_by=auditor,
                note=f"{column_name}:\n\n{row[column_name]}",
            )

    if feedback_survey_sent and feedback_survey_sent != "Yes":
        add_note_to_history(
            detailed_case=detailed_case,
            created=last_updated,
            created_by=auditor,
            note=f"Feedback survey sent:\n\n{feedback_survey_sent}",
        )

    contact: Contact = Contact.objects.create(
        detailed_case=detailed_case,
        name=row["Contact name"],
        job_title=row["Job title"],
        contact_point=row["Contact detail"],
        created_by=auditor,
    )
    contact.created = last_updated
    contact.save()

    zendesk_urls: str = row["Zendesk ticket"]
    for zendesk_url in zendesk_urls.split():
        if zendesk_url.startswith(ZENDESK_URL_PREFIX):
            ZendeskTicket.objects.create(
                detailed_case=detailed_case,
                url=zendesk_url,
                summary="Imported from spreadsheet",
            )


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
    ZendeskTicket.objects.all().delete()
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
