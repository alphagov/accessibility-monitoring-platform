# Generated by Django 4.1.1 on 2022-09-23 08:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0041_case_previous_case_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="case",
            name="report_methodology",
            field=models.CharField(
                choices=[
                    ("platform", "Platform (requires Platform in testing methodology)"),
                    ("odt", "ODT templates"),
                ],
                default="platform",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="case",
            name="testing_methodology",
            field=models.CharField(
                choices=[
                    ("platform", "Platform"),
                    ("spreadsheet", "Testing spreadsheet"),
                ],
                default="platform",
                max_length=20,
            ),
        ),
    ]
