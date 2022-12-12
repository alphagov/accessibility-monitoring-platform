"""Populate case events with data from events"""
import json

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ....cases.models import Case, CaseEvent, CASE_EVENT_TYPE_CREATE, CASE_EVENT_AUDITOR, CASE_EVENT_CREATE_AUDIT
from ...models import Event, EVENT_TYPE_MODEL_UPDATE


class Command(BaseCommand):
    """Django command to cleanup the events"""

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """Reset database for integration tests"""
        CaseEvent.objects.all().delete()
        users = {user.id: user for user in User.objects.all()}  # type: ignore
        for event in Event.objects.all():
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
                        if old_auditor != new_auditor:
                            case: Case = Case.objects.get(id=case_id)
                            CaseEvent.objects.create(
                                case=case,
                                created_by=event.created_by,
                                type=CASE_EVENT_AUDITOR,
                                message=f"Auditor changed from {old_auditor} to {new_auditor}",
                            )
            else:
                new = json.loads(value["new"])[0]
                if new["model"] == "cases.case":
                    case_id = new["pk"]
                    case: Case = Case.objects.get(id=case_id)
                    CaseEvent.objects.create(
                        case=case,
                        created_by=event.created_by,
                        type=CASE_EVENT_TYPE_CREATE,
                    )
                if new["model"] == "audits.audit":
                    case_id = new["fields"]["case"]
                    case: Case = Case.objects.get(id=case_id)
                    CaseEvent.objects.create(
                        case=case,
                        created_by=event.created_by,
                        type=CASE_EVENT_CREATE_AUDIT,
                        message="Start of test",
                    )
