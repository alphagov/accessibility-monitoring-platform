# Generated by Django 4.2.8 on 2024-01-23 14:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audits", "0038_retestpage_additional_issues_notes"),
    ]

    operations = [
        migrations.AddField(
            model_name="wcagdefinition",
            name="hint",
            field=models.TextField(blank=True, default=""),
        ),
    ]
