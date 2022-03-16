# Generated by Django 4.0.2 on 2022-03-16 09:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("cases", "0027_report_generator"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BaseTemplate",
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
                ("created", models.DateTimeField(auto_now_add=True)),
                ("name", models.TextField()),
                ("content", models.TextField(blank=True, default="")),
                ("position", models.IntegerField()),
            ],
            options={
                "ordering": ["position", "-id"],
            },
        ),
        migrations.CreateModel(
            name="Report",
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
                ("created", models.DateTimeField()),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "ready_for_qa",
                    models.CharField(
                        choices=[
                            ("yes", "Yes"),
                            ("no", "No"),
                            ("not-started", "Not started"),
                        ],
                        default="not-started",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True, default="")),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="report_case",
                        to="cases.case",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="report_user",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-id"],
            },
        ),
        migrations.CreateModel(
            name="Section",
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
                ("created", models.DateTimeField(auto_now_add=True)),
                ("name", models.TextField()),
                ("content", models.TextField(blank=True, default="")),
                ("position", models.IntegerField()),
                (
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="section_report",
                        to="reports.report",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
