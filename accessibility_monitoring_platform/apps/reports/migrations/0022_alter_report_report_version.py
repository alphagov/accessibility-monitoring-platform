# Generated by Django 4.1.7 on 2023-04-21 13:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0021_delete_basetemplate"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="report_version",
            field=models.TextField(default="v1_1_0__20230421"),
        ),
    ]
