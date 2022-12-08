"""Delete update events with no changes"""
import json

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ...models import Event, EVENT_TYPE_MODEL_UPDATE


class Command(BaseCommand):
    """Django command to cleanup the events"""

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """Reset database for integration tests"""
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
                            print(
                                f"#{case_id} {event.created} {event.created_by}: Case auditor change from {old_auditor} to {new_auditor}"
                            )
            else:
                new = json.loads(value["new"])[0]
                if new["model"] == "cases.case":
                    case_id = new["pk"]
                    print(
                        f"#{case_id} {event.created} {event.created_by}: Case created"
                    )
