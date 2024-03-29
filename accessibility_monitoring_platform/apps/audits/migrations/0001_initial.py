# Generated by Django 3.2.8 on 2022-01-20 09:48

import datetime

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("cases", "0021_add_audits"),
    ]

    operations = [
        migrations.CreateModel(
            name="Audit",
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
                ("is_deleted", models.BooleanField(default=False)),
                ("date_of_test", models.DateField(default=datetime.date.today)),
                ("name", models.TextField(blank=True, default="")),
                (
                    "screen_size",
                    models.CharField(
                        choices=[("15in", "15 inch"), ("13in", "13 inch")],
                        default="15in",
                        max_length=20,
                    ),
                ),
                (
                    "exemptions_state",
                    models.CharField(
                        choices=[("yes", "Yes"), ("no", "No"), ("unknown", "Unknown")],
                        default="unknown",
                        max_length=20,
                    ),
                ),
                ("exemptions_notes", models.TextField(blank=True, default="")),
                (
                    "type",
                    models.CharField(
                        choices=[("initial", "Initial"), ("retest", "12 week retest")],
                        default="initial",
                        max_length=20,
                    ),
                ),
                (
                    "audit_metadata_complete_date",
                    models.DateField(blank=True, null=True),
                ),
                ("audit_pages_complete_date", models.DateField(blank=True, null=True)),
                (
                    "accessibility_statement_backup_url",
                    models.TextField(blank=True, default=""),
                ),
                (
                    "declaration_state",
                    models.CharField(
                        choices=[
                            ("present", "Present and correct"),
                            ("not-present", "Not included"),
                            ("other", "Other"),
                        ],
                        default="not-present",
                        max_length=20,
                    ),
                ),
                ("declaration_notes", models.TextField(blank=True, default="")),
                (
                    "scope_state",
                    models.CharField(
                        choices=[
                            ("present", "Present and correct"),
                            ("not-present", "Not included"),
                            ("incomplete", "Does not cover entire website"),
                            ("other", "Other"),
                        ],
                        default="not-present",
                        max_length=20,
                    ),
                ),
                ("scope_notes", models.TextField(blank=True, default="")),
                (
                    "compliance_state",
                    models.CharField(
                        choices=[
                            ("present", "Present and correct"),
                            ("incorrect", "Present but incorrect"),
                            ("not-present", "Not present"),
                            ("other", "Other (Please specify)"),
                        ],
                        default="not-present",
                        max_length=20,
                    ),
                ),
                ("compliance_notes", models.TextField(blank=True, default="")),
                (
                    "non_regulation_state",
                    models.CharField(
                        choices=[
                            ("present", "Present and correct"),
                            ("incorrect", "Present but incorrect"),
                            ("not-present", "Not present"),
                            ("n/a", "N/A"),
                            ("other", "Other (Please specify)"),
                        ],
                        default="not-present",
                        max_length=20,
                    ),
                ),
                ("non_regulation_notes", models.TextField(blank=True, default="")),
                (
                    "disproportionate_burden_state",
                    models.CharField(
                        choices=[
                            ("no-claim", "No claim"),
                            ("assessment", "Claim with assessment"),
                            ("no-assessment", "Claim with no assessment"),
                        ],
                        default="no-claim",
                        max_length=20,
                    ),
                ),
                (
                    "disproportionate_burden_notes",
                    models.TextField(blank=True, default=""),
                ),
                (
                    "content_not_in_scope_state",
                    models.CharField(
                        choices=[
                            ("present", "Present and correct"),
                            ("incorrect", "Present but incorrect"),
                            ("not-present", "Not present"),
                            ("n/a", "N/A"),
                            ("other", "Other (Please specify)"),
                        ],
                        default="not-present",
                        max_length=20,
                    ),
                ),
                (
                    "content_not_in_scope_notes",
                    models.TextField(blank=True, default=""),
                ),
                (
                    "preparation_date_state",
                    models.CharField(
                        choices=[
                            ("present", "Present"),
                            ("not-present", "Not included"),
                            ("other", "Other (Please specify)"),
                        ],
                        default="not-present",
                        max_length=20,
                    ),
                ),
                ("preparation_date_notes", models.TextField(blank=True, default="")),
                (
                    "audit_statement_1_complete_date",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "method_state",
                    models.CharField(
                        choices=[
                            ("present", "Present"),
                            ("incomplete", "Present but missing detail"),
                            ("not-present", "Not present"),
                            ("other", "Other (Please specify)"),
                        ],
                        default="not-present",
                        max_length=20,
                    ),
                ),
                ("method_notes", models.TextField(blank=True, default="")),
                (
                    "review_state",
                    models.CharField(
                        choices=[
                            ("present", "Present and correct"),
                            ("not-present", "Not included"),
                            ("n/a", "N/A"),
                            ("other", "Other (Please specify)"),
                        ],
                        default="not-present",
                        max_length=20,
                    ),
                ),
                ("review_notes", models.TextField(blank=True, default="")),
                (
                    "feedback_state",
                    models.CharField(
                        choices=[
                            ("present", "Present"),
                            ("incomplete", "Present but missing detail"),
                            ("not-present", "Not present"),
                            ("other", "Other (Please specify)"),
                        ],
                        default="not-present",
                        max_length=20,
                    ),
                ),
                ("feedback_notes", models.TextField(blank=True, default="")),
                (
                    "contact_information_state",
                    models.CharField(
                        choices=[
                            ("present", "Present"),
                            ("incomplete", "Present but missing detail"),
                            ("not-present", "Not present"),
                            ("other", "Other (Please specify)"),
                        ],
                        default="not-present",
                        max_length=20,
                    ),
                ),
                ("contact_information_notes", models.TextField(blank=True, default="")),
                (
                    "enforcement_procedure_state",
                    models.CharField(
                        choices=[
                            ("present", "Present"),
                            ("not-present", "Not included"),
                            ("other", "Other (Please specify)"),
                        ],
                        default="not-present",
                        max_length=20,
                    ),
                ),
                (
                    "enforcement_procedure_notes",
                    models.TextField(blank=True, default=""),
                ),
                (
                    "access_requirements_state",
                    models.CharField(
                        choices=[
                            ("req-met", "Meets requirements"),
                            ("req-not-met", "Does not meet requirements"),
                            ("n/a", "N/A"),
                            ("other", "Other (Please specify)"),
                        ],
                        default="req-not-met",
                        max_length=20,
                    ),
                ),
                ("access_requirements_notes", models.TextField(blank=True, default="")),
                (
                    "overall_compliance_state",
                    models.CharField(
                        choices=[
                            ("compliant", "Compliant"),
                            ("not-compliant", "Not Compliant"),
                            ("no-statement", "No Statement"),
                        ],
                        default="not-compliant",
                        max_length=20,
                    ),
                ),
                ("overall_compliance_notes", models.TextField(blank=True, default="")),
                (
                    "audit_statement_2_complete_date",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "audit_summary_complete_date",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "accessibility_statement_state",
                    models.CharField(
                        choices=[
                            (
                                "not-found",
                                "An accessibility statement for the website was not found.",
                            ),
                            (
                                "found",
                                "An accessibility statement for the website was found in the correct format.",
                            ),
                            (
                                "found-but",
                                "An accessibility statement for the website was found but:",
                            ),
                        ],
                        default="not-found",
                        max_length=20,
                    ),
                ),
                (
                    "accessibility_statement_not_correct_format",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "accessibility_statement_not_specific_enough",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "accessibility_statement_missing_accessibility_issues",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "accessibility_statement_missing_mandatory_wording",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "accessibility_statement_needs_more_re_disproportionate",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "accessibility_statement_needs_more_re_accessibility",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "accessibility_statement_deadline_not_complete",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "accessibility_statement_deadline_not_sufficient",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "accessibility_statement_out_of_date",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "accessibility_statement_template_update",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "accessibility_statement_accessible",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "accessibility_statement_prominent",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "report_options_next",
                    models.CharField(
                        choices=[
                            ("errors", "Errors were found"),
                            ("no-errors", "No serious errors were found"),
                        ],
                        default="errors",
                        max_length=20,
                    ),
                ),
                (
                    "report_next_change_statement",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "report_next_no_statement",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "report_next_statement_not_right",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "report_next_statement_matches",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "report_next_disproportionate_burden",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "audit_report_options_complete_date",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "audit_report_text_complete_date",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="audit_case",
                        to="cases.case",
                    ),
                ),
                (
                    "retest_of_audit",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="audit_retest",
                        to="audits.audit",
                    ),
                ),
            ],
            options={
                "ordering": ["-id"],
            },
        ),
        migrations.CreateModel(
            name="WcagDefinition",
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
                        choices=[("manual", "Manual"), ("axe", "Axe"), ("pdf", "PDF")],
                        default="manual",
                        max_length=20,
                    ),
                ),
                ("name", models.TextField(blank=True, default="")),
                ("description", models.TextField(blank=True, default="")),
                ("url_on_w3", models.TextField(blank=True, default="")),
                ("report_boilerplate", models.TextField(blank=True, default="")),
                ("date_start", models.DateTimeField(blank=True, null=True)),
                ("date_end", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="Page",
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
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "page_type",
                    models.CharField(
                        choices=[
                            ("extra", "Additional page"),
                            ("home", "Home page"),
                            ("contact", "Contact page"),
                            ("statement", "Accessibility statement"),
                            ("coronavirus", "Coronavirus"),
                            ("pdf", "PDF"),
                            ("form", "Form"),
                        ],
                        default="extra",
                        max_length=20,
                    ),
                ),
                ("name", models.TextField(blank=True, default="")),
                ("url", models.TextField(blank=True, default="")),
                ("complete_date", models.DateField(blank=True, null=True)),
                ("no_errors_date", models.DateField(blank=True, null=True)),
                (
                    "not_found",
                    models.CharField(
                        choices=[("no", "No"), ("yes", "Yes")],
                        default="no",
                        max_length=20,
                    ),
                ),
                (
                    "audit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="page_audit",
                        to="audits.audit",
                    ),
                ),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="CheckResult",
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
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "type",
                    models.CharField(
                        choices=[("manual", "Manual"), ("axe", "Axe"), ("pdf", "PDF")],
                        default="pdf",
                        max_length=20,
                    ),
                ),
                (
                    "check_result_state",
                    models.CharField(
                        choices=[
                            ("error", "Error found"),
                            ("no-error", "No issue"),
                            ("not-tested", "Not tested"),
                        ],
                        default="not-tested",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True, default="")),
                (
                    "audit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checkresult_audit",
                        to="audits.audit",
                    ),
                ),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checkresult_page",
                        to="audits.page",
                    ),
                ),
                (
                    "wcag_definition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checkresult_wcagdefinition",
                        to="audits.wcagdefinition",
                    ),
                ),
            ],
            options={
                "ordering": ["id"],
            },
        ),
    ]
