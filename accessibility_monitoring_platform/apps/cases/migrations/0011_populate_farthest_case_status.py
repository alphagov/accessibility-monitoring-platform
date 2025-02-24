# Generated by Django 5.1.6 on 2025-02-21 08:45

from django.db import migrations


def populate_farthest_case_status(apps, schema_editor):
    CaseStatus = apps.get_model("cases", "CaseStatus")
    case_statuses = CaseStatus.objects.all()
    for case_status in case_statuses:
        case_status.farthest_status = case_status.status
        case_status.save()


def remove_farthest_case_status(apps, schema_editor):  # pylint: disable=unused-argument
    CaseStatus = apps.get_model("cases", "CaseStatus")
    case_statuses = CaseStatus.objects.all()
    for case_status in case_statuses:
        case_status.farthest_status = ""
        case_status.save()


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0010_casestatus_farthest_status_alter_casestatus_status"),
    ]

    operations = [
        migrations.RunPython(
            populate_farthest_case_status, reverse_code=remove_farthest_case_status
        )
    ]
