# Generated by Django 3.2.4 on 2021-07-28 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0005_auto_20210728_0828"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="case",
            name="report_followup_week_12_sent_date",
        ),
        migrations.AddField(
            model_name="case",
            name="twelve_week_update_requested_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
