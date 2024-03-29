# Generated by Django 4.1.4 on 2022-12-12 16:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cases", "0044_remove_case_delete_notes_remove_case_delete_reason_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CaseEvent",
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
                    "event_type",
                    models.CharField(
                        choices=[
                            ("create", "Create"),
                            ("auditor", "Change of auditor"),
                            ("create_audit", "Start test"),
                            ("create_report", "Create report"),
                            ("ready_for_qa", "Report readiness for QA"),
                            ("qa_auditor", "Change of QA auditor"),
                            ("approve_report", "Report approval"),
                            ("retest", "Start retest"),
                            ("read_for_final_decision", "Ready for final decision"),
                            ("completed", "Completed"),
                        ],
                        default="create",
                        max_length=100,
                    ),
                ),
                ("message", models.TextField(blank=True, default="Created case")),
                ("event_time", models.DateTimeField(auto_now_add=True)),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="cases.case"
                    ),
                ),
                (
                    "done_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="case_event_done_by_user",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["event_time"],
            },
        ),
    ]
