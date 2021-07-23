# Generated by Django 3.2.4 on 2021-07-21 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0014_auto_20210721_1328"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="case",
            name="is_case_completed",
        ),
        migrations.RemoveField(
            model_name="case",
            name="is_website_retested",
        ),
        migrations.AddField(
            model_name="case",
            name="case_completed",
            field=models.CharField(
                choices=[
                    (
                        "no-action",
                        "No further action is required and the case can be marked as complete",
                    ),
                    (
                        "escalated",
                        "The audit needs to be sent to the relevant equalities body",
                    ),
                    ("no-decision", "Decision not reached"),
                ],
                default="no-decision",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="case",
            name="escalation_state",
            field=models.CharField(
                choices=[
                    (
                        "no-action",
                        "No further action is required and correspondence has closed regarding this issue",
                    ),
                    ("ongoing", "Correspondence ongoing"),
                    ("unknown", "Not known"),
                ],
                default="unknown",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="case",
            name="retested_website",
            field=models.DateField(blank=True, null=True),
        ),
    ]
