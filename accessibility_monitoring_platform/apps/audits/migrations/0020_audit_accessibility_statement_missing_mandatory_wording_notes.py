# Generated by Django 4.1.2 on 2022-10-28 08:10

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audits", "0019_rename_is_form_page_is_contact_page"),
    ]

    operations = [
        migrations.AddField(
            model_name="audit",
            name="accessibility_statement_missing_mandatory_wording_notes",
            field=models.TextField(blank=True, default=""),
        ),
    ]
