# Generated by Django 4.1a1 on 2022-06-07 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("s3_read_write", "0002_remove_s3report_platform_version"),
    ]

    operations = [
        migrations.AddField(
            model_name="s3report",
            name="html",
            field=models.TextField(blank=True, default=""),
        ),
    ]
