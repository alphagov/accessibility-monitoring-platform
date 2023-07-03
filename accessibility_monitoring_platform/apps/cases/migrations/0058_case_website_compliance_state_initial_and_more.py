# Generated by Django 4.1.7 on 2023-05-26 12:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0057_case_seven_day_no_contact_email_sent_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="case",
            name="website_compliance_state_initial",
            field=models.CharField(
                choices=[
                    ("compliant", "Fully compliant"),
                    ("partially-compliant", "Partially compliant"),
                    ("not-known", "Not known"),
                ],
                default="not-known",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="case",
            name="website_state_final",
            field=models.CharField(
                choices=[
                    ("compliant", "Fully compliant"),
                    ("partially-compliant", "Partially compliant"),
                    ("not-known", "Not known"),
                ],
                default="not-known",
                max_length=200,
            ),
        ),
    ]
