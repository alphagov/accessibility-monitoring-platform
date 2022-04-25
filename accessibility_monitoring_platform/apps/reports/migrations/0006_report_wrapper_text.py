# Generated by Django 4.0.2 on 2022-04-25 07:48

from django.db import migrations


REPORT_WRAPPER_TEXT = {
    "title": "Accessibility report for {{ report.case.domain }}",
    "title_caption": "Accessibility report",
    "sub_header": "Accessibility report",
    "sent_by": "[Government Digital Service](https://www.gov.uk/government/organisations/government-digital-service)",
    "contact": "[accessibility-monitoring-team@gov.uk](mailto:accessibility-monitoring-team@gov.uk)",
    "related_content": """
* [Government Digital Service](https://www.gov.uk/government/organisations/government-digital-service)
* [Government Digital Service](https://www.gov.uk/government/organisations/government-digital-service)
* [Government Digital Service](https://www.gov.uk/government/organisations/government-digital-service)
    """,
}


def populate_report_wrapper(apps, schema_editor):  # pylint: disable=unused-argument
    ReportWrapper = apps.get_model("reports", "ReportWrapper")
    ReportWrapper.objects.create(**REPORT_WRAPPER_TEXT)


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    ReportWrapper = apps.get_model("reports", "ReportWrapper")
    ReportWrapper.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0005_reportwrapper_alter_report_report_version'),
    ]

    operations = [
        migrations.RunPython(populate_report_wrapper, reverse_code=reverse_code),
    ]
