# Generated by Django 4.1.7 on 2023-05-15 08:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0054_update_report_review_choices"),
    ]

    operations = [
        migrations.AlterField(
            model_name="case",
            name="report_review_status",
            field=models.CharField(
                choices=[("yes", "Yes"), ("no", "No")], default="no", max_length=200
            ),
        ),
    ]
