# Generated by Django 3.2.8 on 2021-12-08 14:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0007_auto_20211022_0851"),
        ("cases", "0017_remove_case_service_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="case",
            name="sector",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="common.sector",
            ),
        ),
    ]
