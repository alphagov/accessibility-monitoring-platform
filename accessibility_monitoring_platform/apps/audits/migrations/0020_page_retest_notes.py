# Generated by Django 4.1.2 on 2022-10-27 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audits", "0019_rename_is_form_page_is_contact_page"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="retest_notes",
            field=models.TextField(blank=True, default=""),
        ),
    ]
