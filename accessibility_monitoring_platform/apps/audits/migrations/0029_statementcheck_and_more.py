# Generated by Django 4.1.7 on 2023-06-13 10:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audits", "0028_audit_accessibility_statement_report_text_wording"),
    ]

    operations = [
        migrations.CreateModel(
            name="StatementCheck",
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
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("overview", "Statement overview"),
                            ("website", "Accessibility statement for [website.com]"),
                            ("compliance", "Compliance status"),
                            ("non-accessible", "Non-accessible content"),
                            (
                                "preparation",
                                "Preparation of this accessibility statement",
                            ),
                            ("feedback", "Feedback and enforcement procedure"),
                            ("custom", "Custom statement issues"),
                        ],
                        default="custom",
                        max_length=20,
                    ),
                ),
                ("label", models.TextField(blank=True, default="")),
                ("success_criteria", models.TextField(blank=True, default="")),
                ("report_text", models.TextField(blank=True, default="")),
                ("position", models.IntegerField(default=0)),
                ("is_deleted", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["position", "id"],
            },
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_retest_statement_compliance_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_retest_statement_feedback_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_retest_statement_non_accessible_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_retest_statement_custom_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_retest_statement_overview_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_retest_statement_preparation_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_retest_statement_website_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_statement_compliance_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_statement_feedback_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_statement_non_accessible_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_statement_custom_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_statement_overview_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_statement_preparation_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_statement_website_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="StatementCheckResult",
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
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("overview", "Statement overview"),
                            ("website", "Accessibility statement for [website.com]"),
                            ("compliance", "Compliance status"),
                            ("non-accessible", "Non-accessible content"),
                            (
                                "preparation",
                                "Preparation of this accessibility statement",
                            ),
                            ("feedback", "Feedback and enforcement procedure"),
                            ("custom", "Custom statement issues"),
                        ],
                        default="custom",
                        max_length=20,
                    ),
                ),
                (
                    "check_result_state",
                    models.CharField(
                        choices=[
                            ("yes", "Yes"),
                            ("no", "No"),
                            ("not-tested", "Not tested"),
                        ],
                        default="not-tested",
                        max_length=10,
                    ),
                ),
                ("report_comment", models.TextField(blank=True, default="")),
                ("auditor_notes", models.TextField(blank=True, default="")),
                (
                    "retest_state",
                    models.CharField(
                        choices=[
                            ("yes", "Yes"),
                            ("no", "No"),
                            ("not-tested", "Not tested"),
                        ],
                        default="not-tested",
                        max_length=10,
                    ),
                ),
                ("retest_comment", models.TextField(blank=True, default="")),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "audit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="audits.audit"
                    ),
                ),
                (
                    "statement_check",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="audits.statementcheck",
                        blank=True,
                        null=True,
                    ),
                ),
            ],
            options={
                "ordering": ["id"],
            },
        ),
    ]
