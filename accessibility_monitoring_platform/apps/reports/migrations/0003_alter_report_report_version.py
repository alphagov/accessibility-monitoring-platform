# Generated by Django 5.0.7 on 2024-07-23 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0002_report_wrapper_text"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="report_version",
            field=models.TextField(default="v1_3_0__20240710"),
        ),
    ]
