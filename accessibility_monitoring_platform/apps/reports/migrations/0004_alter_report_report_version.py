# Generated by Django 5.1.1 on 2024-09-30 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0003_alter_report_report_version"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="report_version",
            field=models.TextField(default="v1_4_0__20241005"),
        ),
    ]