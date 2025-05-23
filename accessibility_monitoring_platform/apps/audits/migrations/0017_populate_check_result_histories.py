# Generated by Django 5.2 on 2025-04-29 15:03
import ast
import json

from django.db import migrations
from django.db.models import Q

CHECK_RESULT_CONTENT_TYPE_ID: int = 51
UPDATE_SEPARATOR: str = " -> "
RETEST_STATE_DEFAULT: str = "not-fixed"


def populate_retest_notes_history(apps, schema_editor):
    Event = apps.get_model("common", "Event")
    CheckResult = apps.get_model("audits", "CheckResult")
    CheckResultNotesHistory = apps.get_model("audits", "CheckResultNotesHistory")
    CheckResultRetestNotesHistory = apps.get_model(
        "audits", "CheckResultRetestNotesHistory"
    )
    count: int = 0
    for event in (
        Event.objects.filter(content_type_id=CHECK_RESULT_CONTENT_TYPE_ID)
        .filter(Q(value__contains='"notes"') | Q(value__contains="'notes'"))
        .order_by("created")
    ):
        try:
            value_dict: dict[str, str] = json.loads(event.value)
        except json.decoder.JSONDecodeError:
            value_dict: dict[str, str] = ast.literal_eval(event.value)
        if "notes" in value_dict:
            notes: str = value_dict["notes"]
            if UPDATE_SEPARATOR in notes:
                _, notes = notes.split(UPDATE_SEPARATOR)
        else:
            continue
        check_result: CheckResult = CheckResult.objects.get(id=event.object_id)
        check_result_history: CheckResultNotesHistory = (
            CheckResultNotesHistory.objects.create(
                check_result=check_result,
                notes=notes,
                created_by=event.created_by,
            )
        )
        check_result_history.created = event.created
        check_result_history.save()
        count += 1
        if count % 1000 == 0:
            print(f"{count} notes history entries created")
    count: int = 0
    for event in (
        Event.objects.filter(content_type_id=CHECK_RESULT_CONTENT_TYPE_ID)
        .filter(type="model_update")
        .filter(value__contains="retest_notes")
        .order_by("created")
    ):
        value_dict: dict[str, str] = ast.literal_eval(event.value)
        if "retest_notes" in value_dict:
            _, retest_notes = value_dict["retest_notes"].split(" -> ")
        else:
            continue
        if "retest_state" in value_dict:
            _, retest_state = value_dict["retest_state"].split(" -> ")
        else:
            retest_state: str = RETEST_STATE_DEFAULT
        check_result: CheckResult = CheckResult.objects.get(id=event.object_id)
        check_result_history: CheckResultRetestNotesHistory = (
            CheckResultRetestNotesHistory.objects.create(
                check_result=check_result,
                retest_state=retest_state,
                retest_notes=retest_notes,
                created_by=event.created_by,
            )
        )
        check_result_history.created = event.created
        check_result_history.save()
        count += 1
        if count % 1000 == 0:
            print(f"{count} retest_notes history entries created")


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    CheckResultNotesHistory = apps.get_model("audits", "CheckResultNotesHistory")
    CheckResultRetestNotesHistory = apps.get_model(
        "audits", "CheckResultRetestNotesHistory"
    )
    CheckResultNotesHistory.objects.all().delete()
    CheckResultRetestNotesHistory.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("audits", "0016_checkresultnoteshistory_and_more"),
        ("common", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(populate_retest_notes_history, reverse_code=reverse_code),
    ]
