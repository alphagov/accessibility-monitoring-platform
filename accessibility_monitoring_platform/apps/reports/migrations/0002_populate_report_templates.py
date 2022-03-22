"""
Populate the reports BaseTemplate table with data from a csv
"""
import csv

from django.db import migrations

INPUT_FILE_NAME = "accessibility_monitoring_platform/apps/reports/management/commands/base_templates.csv"

INPUT_FILE_NAME = "accessibility_monitoring_platform/apps/reports/base_templates.csv"
FIELD_NAMES = ["name", "template_type", "content", "position"]


def populate_base_templates(apps, schema_editor):  # pylint: disable=unused-argument
    BaseTemplate = apps.get_model("reports", "BaseTemplate")
    with open(INPUT_FILE_NAME) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                base_template = BaseTemplate.objects.get(id=row["id"])
                for field_name in FIELD_NAMES:
                    setattr(base_template, field_name, row[field_name])
                base_template.save()
            except BaseTemplate.DoesNotExist:
                fields = {field_name: row[field_name] for field_name in FIELD_NAMES}
                fields["id"] = row["id"]
                BaseTemplate.objects.create(**fields)


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0001_report_generator"),
    ]

    operations = [
        migrations.RunPython(populate_base_templates, reverse_code=reverse_code),
    ]
