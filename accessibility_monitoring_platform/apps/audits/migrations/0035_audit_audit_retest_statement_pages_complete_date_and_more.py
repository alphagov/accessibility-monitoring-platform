# Generated by Django 4.2.4 on 2023-11-28 11:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("audits", "0034_audit_statement_extra_report_text"),
    ]

    operations = [
        migrations.AddField(
            model_name="audit",
            name="audit_retest_statement_pages_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="audit",
            name="audit_statement_pages_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="StatementPage",
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
                ("url", models.TextField(blank=True, default="")),
                ("backup_url", models.TextField(blank=True, default="")),
                (
                    "added_stage",
                    models.CharField(
                        choices=[
                            ("initial", "Initial"),
                            ("12-week-retest", "12-week retest"),
                            ("retest", "Equality body retest"),
                        ],
                        default="initial",
                        max_length=20,
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "audit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="statementpage_audit",
                        to="audits.audit",
                    ),
                ),
            ],
            options={
                "ordering": ["-id"],
            },
        ),
    ]
