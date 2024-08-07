# Generated by Django 5.0.7 on 2024-07-18 09:33

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("cases", "0004_case_no_contact_four_week_chaser_due_date_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationSetting",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        primary_key=True,
                        related_name="notification_settings_user",
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("email_notifications_enabled", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "NotificationSetting",
                "verbose_name_plural": "NotificationSettings",
            },
        ),
        migrations.CreateModel(
            name="Task",
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
                            ("qa-comment", "QA comment"),
                            ("report-approved", "Report approved"),
                            ("reminder", "Reminder"),
                            ("overdue", "Overdue"),
                            ("postcase", "Post case"),
                        ],
                        default="reminder",
                        max_length=20,
                    ),
                ),
                ("date", models.DateField()),
                ("description", models.TextField(default="")),
                ("read", models.BooleanField(default=False)),
                ("action", models.TextField(default="N/A")),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "case",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="cases.case",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-id"],
            },
        ),
    ]
