# Generated by Django 5.1.1 on 2024-09-30 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "audits",
            "0004_rename_audit_summary_complete_date_audit_audit_statement_summary_complete_date_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="checkresult",
            name="id_within_case",
            field=models.IntegerField(blank=True, default=0),
        ),
    ]