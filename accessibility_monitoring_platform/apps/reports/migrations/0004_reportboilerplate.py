# Generated by Django 4.0.2 on 2022-04-19 12:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0003_remove_report_ready_for_qa"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportBoilerplate",
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
                ("title", models.TextField(blank=True, default="")),
                ("title_caption", models.TextField(blank=True, default="")),
                ("sub_header", models.TextField(blank=True, default="")),
                ("sent_by", models.TextField(blank=True, default="")),
                ("contact", models.TextField(blank=True, default="")),
                ("related_content", models.TextField(blank=True, default="")),
            ],
            options={
                "ordering": ["-id"],
            },
        ),
    ]
