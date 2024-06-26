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
            name="S3Report",
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
                ("s3_directory", models.TextField(blank=True, default="")),
                ("version", models.IntegerField(blank=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("latest_published", models.BooleanField(default=False)),
                ("guid", models.CharField(blank=True, max_length=40)),
                ("html", models.TextField(blank=True, default="")),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="cases.case"
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="report_created_by_user",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
