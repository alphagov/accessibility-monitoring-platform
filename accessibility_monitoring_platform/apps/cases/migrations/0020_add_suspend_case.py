# Generated by Django 3.2.8 on 2021-12-24 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0019_alter_case_psb_location"),
    ]

    operations = [
        migrations.AddField(
            model_name="case",
            name="is_suspended",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="case",
            name="suspend_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="case",
            name="suspend_notes",
            field=models.TextField(blank=True, default=""),
        ),
    ]
