# Generated by Django 4.1.7 on 2023-04-21 13:08

from django.db import migrations


def upgrade_report_version(apps, schema_editor):  # pylint: disable=unused-argument
    """Populate case events with data from events"""
    # pylint: disable=invalid-name
    Report = apps.get_model("reports", "Report")
    for report in Report.objects.all():
        report.report_version = "v1_1_0__20230421"
        report.save()


def downgrade_report_version(apps, schema_editor):  # pylint: disable=unused-argument
    """Delete all case events"""
    # pylint: disable=invalid-name
    Report = apps.get_model("reports", "Report")
    for report in Report.objects.all():
        report.report_version = "v1_0_0__20220406"
        report.save()


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0022_alter_report_report_version"),
    ]

    operations = [
        migrations.RunPython(
            upgrade_report_version, reverse_code=downgrade_report_version
        ),
    ]