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
                    if old["model"] == "cases.case":
                        case_id = old["pk"]
                        old_auditor = users.get(old["fields"]["auditor"], "None")
                        new_auditor = users.get(new["fields"]["auditor"], "None")
                        old_review_status = old["fields"]["report_review_status"]
                        new_review_status = new["fields"]["report_review_status"]
                        case: Case = Case.objects.get(id=case_id)
                        with patch("django.utils.timezone.now", Mock(return_value=event.created)):
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
            else:
                new = json.loads(value["new"])[0]
                if new["model"] == "cases.case":
                    case_id = new["pk"]
                    case: Case = Case.objects.get(id=case_id)
                    with patch("django.utils.timezone.now", Mock(return_value=event.created)):
                        CaseEvent.objects.create(
                            case=case,
                            created=event.created,
                            created_by=event.created_by,
                            type=CASE_EVENT_TYPE_CREATE,
                        )
                if new["model"] == "audits.audit":
                    case_id = new["fields"]["case"]
                    case: Case = Case.objects.get(id=case_id)
                    with patch("django.utils.timezone.now", Mock(return_value=event.created)):
                        CaseEvent.objects.create(
                            case=case,
                            created_by=event.created_by,
                            type=CASE_EVENT_CREATE_AUDIT,
                            message="Started test",
                        )
                if new["model"] == "reports.report":
                    case_id = new["fields"]["case"]
                    case: Case = Case.objects.get(id=case_id)
                    with patch("django.utils.timezone.now", Mock(return_value=event.created)):
                        CaseEvent.objects.create(
                            case=case,
                            created_by=event.created_by,
                            type=CASE_EVENT_CREATE_REPORT,
                            message="Created report",
                        )
