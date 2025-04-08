# Generated by Django 5.1.8 on 2025-04-08 06:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0004_rename_description_issuereport_issue_description_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="emailtemplate",
            name="slug",
        ),
        migrations.RemoveField(
            model_name="emailtemplate",
            name="template",
        ),
        migrations.RemoveField(
            model_name="emailtemplate",
            name="type",
        ),
        migrations.AddField(
            model_name="emailtemplate",
            name="template_name",
            field=models.CharField(default="", max_length=250),
        ),
    ]
