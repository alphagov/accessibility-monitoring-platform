# Generated by Django 5.0.4 on 2024-06-05 08:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("cases", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Reminder",
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
                ("due_date", models.DateField()),
                ("description", models.TextField()),
                ("is_deleted", models.BooleanField(default=False)),
                ("updated", models.DateTimeField(blank=True, null=True)),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reminder_case",
                        to="cases.case",
                    ),
                ),
            ],
            options={
                "ordering": ["-id"],
            },
        ),
    ]
