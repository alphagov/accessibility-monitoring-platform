# Generated by Django 5.1.6 on 2025-02-21 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0009_update_case_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="casestatus",
            name="farthest_status",
            field=models.CharField(
                choices=[
                    ("000-unknown", "Unknown"),
                    ("010-unassigned-case", "Unassigned case"),
                    ("020-test-in-progress", "Test in progress"),
                    ("030-report-in-progress", "Report in progress"),
                    ("040-unassigned-qa-case", "Report ready to QA"),
                    ("050-qa-in-progress", "QA in progress"),
                    ("060-report-ready-to-send", "Report ready to send"),
                    ("070-in-report-correspondence", "Report sent"),
                    (
                        "080-in-probation-period",
                        "Report acknowledged waiting for 12-week deadline",
                    ),
                    ("090-in-12-week-correspondence", "After 12-week correspondence"),
                    ("100-reviewing-changes", "Reviewing changes"),
                    ("110-final-decision-due", "Final decision due"),
                    (
                        "120-case-closed-waiting-to-be-sent",
                        "Case closed and waiting to be sent to equalities body",
                    ),
                    (
                        "130-case-closed-sent-to-equalities-body",
                        "Case closed and sent to equalities body",
                    ),
                    (
                        "140-in-correspondence-with-equalities-body",
                        "In correspondence with equalities body",
                    ),
                    ("150-complete", "Complete"),
                    ("160-deactivated", "Deactivated"),
                ],
                default="010-unassigned-case",
                max_length=200,
            ),
        ),
        migrations.AlterField(
            model_name="casestatus",
            name="status",
            field=models.CharField(
                choices=[
                    ("000-unknown", "Unknown"),
                    ("010-unassigned-case", "Unassigned case"),
                    ("020-test-in-progress", "Test in progress"),
                    ("030-report-in-progress", "Report in progress"),
                    ("040-unassigned-qa-case", "Report ready to QA"),
                    ("050-qa-in-progress", "QA in progress"),
                    ("060-report-ready-to-send", "Report ready to send"),
                    ("070-in-report-correspondence", "Report sent"),
                    (
                        "080-in-probation-period",
                        "Report acknowledged waiting for 12-week deadline",
                    ),
                    ("090-in-12-week-correspondence", "After 12-week correspondence"),
                    ("100-reviewing-changes", "Reviewing changes"),
                    ("110-final-decision-due", "Final decision due"),
                    (
                        "120-case-closed-waiting-to-be-sent",
                        "Case closed and waiting to be sent to equalities body",
                    ),
                    (
                        "130-case-closed-sent-to-equalities-body",
                        "Case closed and sent to equalities body",
                    ),
                    (
                        "140-in-correspondence-with-equalities-body",
                        "In correspondence with equalities body",
                    ),
                    ("150-complete", "Complete"),
                    ("160-deactivated", "Deactivated"),
                ],
                default="010-unassigned-case",
                max_length=200,
            ),
        ),
    ]
