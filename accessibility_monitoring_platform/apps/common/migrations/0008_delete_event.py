# Generated by Django 5.2 on 2025-04-28 08:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0007_populate_template_name"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Event",
        ),
    ]
