"""Populate case events with data from events"""
import json
from unittest.mock import patch, Mock

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ....cases.models import (
    Case,
    CaseEvent,
    CASE_EVENT_TYPE_CREATE,
    CASE_EVENT_AUDITOR,
    CASE_EVENT_CREATE_AUDIT,
    CASE_EVENT_CREATE_REPORT,
    CASE_EVENT_READY_FOR_QA,
    CASE_EVENT_QA_AUDITOR,
    CASE_EVENT_APPROVE_REPORT,
    CASE_EVENT_START_RETEST,
    CASE_EVENT_READY_FOR_FINAL_DECISION,
    CASE_EVENT_CASE_COMPLETED,
)
from ...models import Event, EVENT_TYPE_MODEL_UPDATE


class Command(BaseCommand):
    """Django command to cleanup the events"""

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """Reset database for integration tests"""
        CaseEvent.objects.all().delete()
        users = {user.id: user for user in User.objects.all()}  # type: ignore
        for event in Event.objects.all().order_by("id"):
            value = json.loads(event.value)
            if event.type == EVENT_TYPE_MODEL_UPDATE:
                if value["old"] == value["new"]:
                    event.delete()
                else:
                    old = json.loads(value["old"])[0]
                    new = json.loads(value["new"])[0]
                    with patch(
                        "django.utils.timezone.now", Mock(return_value=event.created)
                    ):
                        if old["model"] == "cases.case":
                            case_id = old["pk"]
                            old_auditor = users.get(old["fields"]["auditor"], "None")
                            new_auditor = users.get(new["fields"]["auditor"], "None")
                            old_review_status = old["fields"]["report_review_status"]
                            new_review_status = new["fields"]["report_review_status"]
                            old_reviewer = users.get(old["fields"]["reviewer"], "None")
                            new_reviewer = users.get(new["fields"]["reviewer"], "None")
                            old_is_ready_for_final_decision = old["fields"][
                                "is_ready_for_final_decision"
                            ]
                            new_is_ready_for_final_decision = new["fields"][
                                "is_ready_for_final_decision"
                            ]
                            old_case_completed = old["fields"]["case_completed"]
                            new_case_completed = new["fields"]["case_completed"]
                            old_report_approved_status = old["fields"][
                                "report_approved_status"
                            ]
                            new_report_approved_status = new["fields"][
                                "report_approved_status"
                            ]
                            case: Case = Case.objects.get(id=case_id)
                            if old_auditor != new_auditor:
                                CaseEvent.objects.create(
                                    case=case,
                                    created_by=event.created_by,
                                    type=CASE_EVENT_AUDITOR,
                                    message=f"Auditor changed from {old_auditor} to {new_auditor}",
                                )
                            if old_review_status != new_review_status:
                                CaseEvent.objects.create(
                                    case=case,
                                    created_by=event.created_by,
                                    type=CASE_EVENT_READY_FOR_QA,
                                    message=f"Report ready to be reviewed changed from '{old_review_status}' to '{new_review_status}'",
                                )
                            if old_reviewer != new_reviewer:
                                CaseEvent.objects.create(
                                    case=case,
                                    created_by=event.created_by,
                                    type=CASE_EVENT_QA_AUDITOR,
                                    message=f"QA auditor changed from {old_reviewer} to {new_reviewer}",
                                )
                            if old_report_approved_status != new_report_approved_status:
                                CaseEvent.objects.create(
                                    case=case,
                                    created_by=event.created_by,
                                    type=CASE_EVENT_APPROVE_REPORT,
                                    message=f"Report approved changed from '{old_report_approved_status}' to '{new_report_approved_status}'",
                                )
                            if (
                                old_is_ready_for_final_decision
                                != new_is_ready_for_final_decision
                            ):
                                CaseEvent.objects.create(
                                    case=case,
                                    created_by=event.created_by,
                                    type=CASE_EVENT_READY_FOR_FINAL_DECISION,
                                    message=f"Case ready for final decision changed from '{old_is_ready_for_final_decision}' to '{new_is_ready_for_final_decision}'",
                                )
                            if old_case_completed != new_case_completed:
                                CaseEvent.objects.create(
                                    case=case,
                                    created_by=event.created_by,
                                    type=CASE_EVENT_CASE_COMPLETED,
                                    message=f"Case completed changed from '{old_case_completed}' to '{new_case_completed}'",
                                )
                        if old["model"] == "audits.audit":
                            case_id = new["fields"]["case"]
                            case: Case = Case.objects.get(id=case_id)
                            old_retest_date = old["fields"]["retest_date"]
                            new_retest_date = new["fields"]["retest_date"]
                            if old_retest_date != new_retest_date:
                                CaseEvent.objects.create(
                                    case=case,
                                    created_by=event.created_by,
                                    type=CASE_EVENT_START_RETEST,
                                    message=f"Started retest (set to {new_retest_date})",
                                )
            else:
                new = json.loads(value["new"])[0]
                if new["model"] == "cases.case":
                    case_id = new["pk"]
                    case: Case = Case.objects.get(id=case_id)
                    with patch(
                        "django.utils.timezone.now", Mock(return_value=event.created)
                    ):
                        CaseEvent.objects.create(
                            case=case,
                            created=event.created,
                            created_by=event.created_by,
                            type=CASE_EVENT_TYPE_CREATE,
                        )
                if new["model"] == "audits.audit":
                    case_id = new["fields"]["case"]
                    case: Case = Case.objects.get(id=case_id)
                    with patch(
                        "django.utils.timezone.now", Mock(return_value=event.created)
                    ):
                        CaseEvent.objects.create(
                            case=case,
                            created_by=event.created_by,
                            type=CASE_EVENT_CREATE_AUDIT,
                            message="Started test",
                        )
                if new["model"] == "reports.report":
                    case_id = new["fields"]["case"]
                    case: Case = Case.objects.get(id=case_id)
                    with patch(
                        "django.utils.timezone.now", Mock(return_value=event.created)
                    ):
                        CaseEvent.objects.create(
                            case=case,
                            created_by=event.created_by,
                            type=CASE_EVENT_CREATE_REPORT,
                            message="Created report",
                        )
