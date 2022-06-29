# Generated by Django 4.1a1 on 2022-06-28 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audits", "0010_alter_page_page_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="audit",
            name="audit_retest_review_state",
            field=models.CharField(
                choices=[
                    ("present", "Present and correct"),
                    ("out-of-date", "Present but out of date"),
                    ("not-present", "Not included"),
                    ("n/a", "N/A"),
                    ("other", "Other (Please specify)"),
                ],
                default="not-present",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="audit",
            name="review_state",
            field=models.CharField(
                choices=[
                    ("present", "Present and correct"),
                    ("out-of-date", "Present but out of date"),
                    ("not-present", "Not included"),
                    ("n/a", "N/A"),
                    ("other", "Other (Please specify)"),
                ],
                default="not-present",
                max_length=20,
            ),
        ),
    ]
