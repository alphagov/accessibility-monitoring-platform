"""
Populate the WcagDefinitions table with data from a csv
"""
import csv

from django.db import migrations

INPUT_FILE_NAME = (
    "accessibility_monitoring_platform/apps/audits/wcag_definitions.csv"
)


def populate_wcag_definitions(apps, schema_editor):  # pylint: disable=unused-argument
    WcagDefinition = apps.get_model("audits", "WcagDefinition")
    with open(INPUT_FILE_NAME) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                wcag_definition = WcagDefinition.objects.get(id=row["id"])
                wcag_definition.type = row["type"]
                wcag_definition.name = row["name"]
                wcag_definition.description = row["description"]
                wcag_definition.report_boilerplate = row["report_boilerplate"]
                wcag_definition.save()
            except WcagDefinition.DoesNotExist:
                WcagDefinition.objects.create(
                    id=row["id"],
                    type=row["type"],
                    name=row["name"],
                    description=row["description"],
                    report_boilerplate=row["report_boilerplate"],
                )


class Migration(migrations.Migration):

    dependencies = [
        ("audits", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(populate_wcag_definitions),
    ]
