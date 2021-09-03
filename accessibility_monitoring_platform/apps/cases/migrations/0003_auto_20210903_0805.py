# Generated by Django 3.2.4 on 2021-09-03 08:05
from datetime import date

from django.conf import settings
from django.db import migrations

TODAY = date.today()

FLAGS_AND_DATES = [
    ("is_case_details_complete", "case_details_complete_date"),
    ("is_contact_details_complete", "contact_details_complete_date"),
    ("is_testing_details_complete", "testing_details_complete_date"),
    ("is_reporting_details_complete", "reporting_details_complete_date"),
    ("is_report_correspondence_complete", "report_correspondence_complete_date"),
    ("is_12_week_correspondence_complete", "twelve_week_correspondence_complete_date"),
    ("is_final_decision_complete", "final_decision_complete_date"),
    (
        "is_enforcement_correspondence_complete",
        "enforcement_correspondence_complete_date",
    ),
]


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0002_auto_20210903_0800"),
    ]

    def populate_completion_dates(apps, schema_editor):
        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            # This process goes haywire when using sqlite (e.g. setting up test env)
            return
        Case = apps.get_model("cases", "Case")
        for case in Case.objects.all():
            save_case = False
            for completed_flag, completed_date in FLAGS_AND_DATES:
                if getattr(case, completed_flag):
                    setattr(case, completed_date, TODAY)
                    save_case = True
            if save_case:
                case.save()

    operations = [
        migrations.RunPython(populate_completion_dates),
    ]
