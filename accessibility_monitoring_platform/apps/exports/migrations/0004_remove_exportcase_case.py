# Generated by Django 5.2.3 on 2025-07-04 07:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("exports", "0003_populate_simplified_case"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="exportcase",
            name="case",
        ),
    ]
