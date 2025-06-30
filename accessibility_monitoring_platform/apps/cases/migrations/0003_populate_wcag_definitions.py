"""
Populate the WcagDefinitions table with data from a csv
"""

import csv

from django.db import migrations

INPUT_FILE_NAME = "accessibility_monitoring_platform/apps/audits/wcag_definitions.csv"
FIELD_NAMES = ["type", "name", "description", "url_on_w3", "report_boilerplate"]


def populate_wcag_definitions(apps, schema_editor):  # pylint: disable=unused-argument
    WcagDefinition = apps.get_model("audits", "WcagDefinition")
    with open(INPUT_FILE_NAME) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                wcag_definition = WcagDefinition.objects.get(id=row["id"])
                for field_name in FIELD_NAMES:
                    setattr(wcag_definition, field_name, row[field_name])
                wcag_definition.save()
            except WcagDefinition.DoesNotExist:
                fields = {field_name: row[field_name] for field_name in FIELD_NAMES}
                fields["id"] = row["id"]
                WcagDefinition.objects.create(**fields)


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0002_initial"),
        ("audits", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(populate_wcag_definitions, reverse_code=reverse_code),
    ]
