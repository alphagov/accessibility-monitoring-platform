# Generated by Django 4.1.1 on 2022-10-13 14:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0042_alter_case_report_methodology_and_more"),
        ("audits", "0017_delete_dups"),
    ]

    operations = [
        migrations.AlterField(
            model_name="audit",
            name="case",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="audit_case",
                to="cases.case",
            ),
        ),
    ]
