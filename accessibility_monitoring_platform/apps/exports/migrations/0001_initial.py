# Generated by Django 5.0.4 on 2024-06-05 08:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("cases", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Export",
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
                ("cutoff_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[("not", "Not yet exported"), ("exported", "Exported")],
                        default="not",
                        max_length=20,
                    ),
                ),
                (
                    "enforcement_body",
                    models.CharField(
                        choices=[
                            ("ehrc", "Equality and Human Rights Commission"),
                            ("ecni", "Equality Commission Northern Ireland"),
                        ],
                        default="ehrc",
                        max_length=20,
                    ),
                ),
                ("export_date", models.DateField(blank=True, null=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "exporter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="exporter",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-cutoff_date"],
            },
        ),
        migrations.CreateModel(
            name="ExportCase",
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
                    "status",
                    models.CharField(
                        choices=[
                            ("unready", "Unready"),
                            ("ready", "Ready"),
                            ("excluded", "Excluded"),
                        ],
                        default="unready",
                        max_length=20,
                    ),
                ),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="cases.case"
                    ),
                ),
                (
                    "export",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="exports.export"
                    ),
                ),
            ],
            options={
                "ordering": ["id"],
            },
        ),
    ]
