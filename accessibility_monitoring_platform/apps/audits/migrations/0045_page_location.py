# Generated by Django 5.0.4 on 2024-04-23 13:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audits", "0044_alter_retest_statement_compliance_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="location",
            field=models.TextField(blank=True, default=""),
        ),
    ]
