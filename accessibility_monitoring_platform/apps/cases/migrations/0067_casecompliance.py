# Generated by Django 4.2.4 on 2023-10-23 12:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0066_remove_case_test_status_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CaseCompliance",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("version", models.IntegerField(default=0)),
                (
                    "website_compliance_state_initial",
                    models.CharField(
                        choices=[
                            ("compliant", "Fully compliant"),
                            ("partially-compliant", "Partially compliant"),
                            ("not-known", "Not known"),
                        ],
                        default="not-known",
                        max_length=20,
                    ),
                ),
                (
                    "website_compliance_notes_initial",
                    models.TextField(blank=True, default=""),
                ),
                (
                    "statement_compliance_state_initial",
                    models.CharField(
                        choices=[
                            ("compliant", "Compliant"),
                            ("not-compliant", "Not compliant"),
                            ("not-found", "Not found"),
                            ("other", "Other"),
                            ("unknown", "Not selected"),
                        ],
                        default="unknown",
                        max_length=200,
                    ),
                ),
                (
                    "statement_compliance_notes_initial",
                    models.TextField(blank=True, default=""),
                ),
                (
                    "website_compliance_state_12_week",
                    models.CharField(
                        choices=[
                            ("compliant", "Fully compliant"),
                            ("partially-compliant", "Partially compliant"),
                            ("not-known", "Not known"),
                        ],
                        default="not-known",
                        max_length=200,
                    ),
                ),
                (
                    "website_compliance_notes_12_week",
                    models.TextField(blank=True, default=""),
                ),
                (
                    "statement_compliance_state_12_week",
                    models.CharField(
                        choices=[
                            ("compliant", "Compliant"),
                            ("not-compliant", "Not compliant"),
                            ("not-found", "Not found"),
                            ("other", "Other"),
                            ("unknown", "Not selected"),
                        ],
                        default="unknown",
                        max_length=200,
                    ),
                ),
                (
                    "statement_compliance_notes_12_week",
                    models.TextField(blank=True, default=""),
                ),
                (
                    "case",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="compliance",
                        to="cases.case",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
