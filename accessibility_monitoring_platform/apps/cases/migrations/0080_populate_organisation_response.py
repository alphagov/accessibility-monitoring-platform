# Generated by Django 4.2.8 on 2024-01-09 08:52

from django.db import migrations


def populate_organisation_response(
    apps, schema_editor
):  # pylint: disable=unused-argument
    Case = apps.get_model("cases", "Case")
    for case in Case.objects.filter(twelve_week_response_state="yes"):
        case.organisation_response = "no-response"
        case.save()


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0079_case_compliance_decision_sent_to_email_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_organisation_response, reverse_code=reverse_code),
    ]
