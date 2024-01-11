"""Populate new CaseEvent model"""
import json
from datetime import datetime
from typing import Dict
from unittest.mock import Mock, patch

from django.db import migrations

from ...common.models import EVENT_TYPE_MODEL_UPDATE
from ...common.utils import amp_format_date

CASE_EVENT_TYPE_CREATE: str = "create"
CASE_EVENT_AUDITOR: str = "auditor"
CASE_EVENT_CREATE_AUDIT: str = "create_audit"
CASE_EVENT_CREATE_REPORT: str = "create_report"
CASE_EVENT_READY_FOR_QA: str = "ready_for_qa"
CASE_EVENT_QA_AUDITOR: str = "qa_auditor"
CASE_EVENT_APPROVE_REPORT: str = "approve_report"
CASE_EVENT_START_RETEST: str = "retest"
CASE_EVENT_READY_FOR_FINAL_DECISION: str = "read_for_final_decision"
CASE_EVENT_CASE_COMPLETED: str = "completed"

REPORT_REVIEW_STATUS_LABELS: Dict[str, str] = {
    "ready-to-review": "Yes",
    "in-progress": "In progress",
    "not-started": "Not started",
}
BOOLEAN_LABELS: Dict[str, str] = {
    "yes": "Yes",
    "no": "No",
}
CASE_COMPLETED_LABELS: Dict[str, str] = {
    "complete-send": "Case is complete and is ready to send to the equality body",
    "complete-no-send": "Case should not be sent to the equality body",
    "no-decision": "Case still in progress",
}

REPORT_APPROVED_STATUS_LABELS: Dict[str, str] = {
    "yes": "Yes",
    "in-progress": "Further work is needed",
    "not-started": "Not started",
}


def populate_case_events(apps, schema_editor):  # pylint: disable=unused-argument
    """Populate case events with data from events"""
    # pylint: disable=invalid-name
    # pylint: disable=line-too-long
    Event = apps.get_model("common", "Event")
    Case = apps.get_model("cases", "Case")
    CaseEvent = apps.get_model("cases", "CaseEvent")
    User = apps.get_model("auth", "User")

    users: dict[int, str] = {
        user.id: f"{user.first_name} {user.last_name}" for user in User.objects.all()
    }
    # Filter events by the content type to reduce memory needed for this to run.
    # Django content type ids: 26|cases|case, 48|audits|audit, 54|reports|report
    for event in Event.objects.filter(content_type__in=[26, 48, 54]).order_by("id"):
        value: Dict = json.loads(event.value)
        if event.type == EVENT_TYPE_MODEL_UPDATE:
            if value["old"] == value["new"]:
                event.delete()
            else:
                old: Dict = json.loads(value["old"])[0]
                new: Dict = json.loads(value["new"])[0]
                with patch(
                    "django.utils.timezone.now", Mock(return_value=event.created)
                ):
                    if old["model"] == "cases.case":
                        case_id: int = old["pk"]
                        old_auditor: str = users.get(old["fields"]["auditor"], "none")
                        new_auditor: str = users.get(new["fields"]["auditor"], "none")
                        old_review_status: str = REPORT_REVIEW_STATUS_LABELS[
                            old["fields"]["report_review_status"]
                        ]
                        new_review_status: str = REPORT_REVIEW_STATUS_LABELS[
                            new["fields"]["report_review_status"]
                        ]
                        old_reviewer: str = users.get(old["fields"]["reviewer"], "none")
                        new_reviewer: str = users.get(new["fields"]["reviewer"], "none")
                        old_is_ready_for_final_decision: str = BOOLEAN_LABELS[
                            old["fields"]["is_ready_for_final_decision"]
                        ]
                        new_is_ready_for_final_decision: str = BOOLEAN_LABELS[
                            new["fields"]["is_ready_for_final_decision"]
                        ]
                        old_case_completed: str = CASE_COMPLETED_LABELS[
                            old["fields"]["case_completed"]
                        ]
                        new_case_completed: str = CASE_COMPLETED_LABELS[
                            new["fields"]["case_completed"]
                        ]
                        old_report_approved_status: str = REPORT_APPROVED_STATUS_LABELS[
                            old["fields"]["report_approved_status"]
                        ]
                        new_report_approved_status: str = REPORT_APPROVED_STATUS_LABELS[
                            new["fields"]["report_approved_status"]
                        ]
                        case = Case.objects.get(id=case_id)
                        if old_auditor != new_auditor:
                            CaseEvent.objects.create(
                                case=case,
                                done_by=event.created_by,
                                event_type=CASE_EVENT_AUDITOR,
                                message=f"Auditor changed from {old_auditor} to {new_auditor}",
                            )
                        if old_review_status != new_review_status:
                            CaseEvent.objects.create(
                                case=case,
                                done_by=event.created_by,
                                event_type=CASE_EVENT_READY_FOR_QA,
                                message=f"Report ready to be reviewed changed from '{old_review_status}' to '{new_review_status}'",
                            )
                        if old_reviewer != new_reviewer:
                            CaseEvent.objects.create(
                                case=case,
                                done_by=event.created_by,
                                event_type=CASE_EVENT_QA_AUDITOR,
                                message=f"QA auditor changed from {old_reviewer} to {new_reviewer}",
                            )
                        if old_report_approved_status != new_report_approved_status:
                            CaseEvent.objects.create(
                                case=case,
                                done_by=event.created_by,
                                event_type=CASE_EVENT_APPROVE_REPORT,
                                message=f"Report approved changed from '{old_report_approved_status}' to '{new_report_approved_status}'",
                            )
                        if (
                            old_is_ready_for_final_decision
                            != new_is_ready_for_final_decision
                        ):
                            CaseEvent.objects.create(
                                case=case,
                                done_by=event.created_by,
                                event_type=CASE_EVENT_READY_FOR_FINAL_DECISION,
                                message=f"Case ready for final decision changed from '{old_is_ready_for_final_decision}' to '{new_is_ready_for_final_decision}'",
                            )
                        if old_case_completed != new_case_completed:
                            CaseEvent.objects.create(
                                case=case,
                                done_by=event.created_by,
                                event_type=CASE_EVENT_CASE_COMPLETED,
                                message=f"Case completed changed from '{old_case_completed}' to '{new_case_completed}'",
                            )
                    if old["model"] == "audits.audit":
                        case_id: int = new["fields"]["case"]
                        case = Case.objects.get(id=case_id)
                        old_retest_date: str = old["fields"]["retest_date"]
                        new_retest_date: str = new["fields"]["retest_date"]
                        if old_retest_date != new_retest_date:
                            if new_retest_date is None:
                                retest_date: str = "None"
                            else:
                                retest_date: str = amp_format_date(
                                    datetime.strptime(new_retest_date, "%Y-%m-%d")
                                )
                            CaseEvent.objects.create(
                                case=case,
                                done_by=event.created_by,
                                event_type=CASE_EVENT_START_RETEST,
                                message=f"Started retest (set to {retest_date})",
                            )
        else:
            new: Dict = json.loads(value["new"])[0]
            if new["model"] == "cases.case":
                case_id: int = new["pk"]
                case = Case.objects.get(id=case_id)
                with patch(
                    "django.utils.timezone.now", Mock(return_value=event.created)
                ):
                    CaseEvent.objects.create(
                        case=case,
                        done_by=event.created_by,
                        event_type=CASE_EVENT_TYPE_CREATE,
                    )
            if new["model"] == "audits.audit":
                case_id: int = new["fields"]["case"]
                case = Case.objects.get(id=case_id)
                with patch(
                    "django.utils.timezone.now", Mock(return_value=event.created)
                ):
                    CaseEvent.objects.create(
                        case=case,
                        done_by=event.created_by,
                        event_type=CASE_EVENT_CREATE_AUDIT,
                        message="Started test",
                    )
            if new["model"] == "reports.report":
                case_id: int = new["fields"]["case"]
                case = Case.objects.get(id=case_id)
                with patch(
                    "django.utils.timezone.now", Mock(return_value=event.created)
                ):
                    CaseEvent.objects.create(
                        case=case,
                        done_by=event.created_by,
                        event_type=CASE_EVENT_CREATE_REPORT,
                        message="Created report",
                    )


def delete_case_events(apps, schema_editor):  # pylint: disable=unused-argument
    """Delete all case events"""
    # pylint: disable=invalid-name
    CaseEvent = apps.get_model("cases", "CaseEvent")
    CaseEvent.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0045_caseevent"),
    ]

    operations = [
        migrations.RunPython(populate_case_events, reverse_code=delete_case_events),
    ]
