"""
Populate the report boilerplate text
"""
from django.db import migrations


REPORT_BOILERPLATE = {
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


def populate_report_boilerplate(apps, schema_editor):  # pylint: disable=unused-argument
    ReportBoilerplate = apps.get_model("reports", "ReportBoilerplate")
    ReportBoilerplate.objects.all().delete()
    ReportBoilerplate.objects.create(**REPORT_BOILERPLATE)


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0004_reportboilerplate"),
    ]

    operations = [
        migrations.RunPython(populate_report_boilerplate, reverse_code=reverse_code),
    ]
