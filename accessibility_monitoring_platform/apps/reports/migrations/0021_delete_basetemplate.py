# Generated by Django 4.1.7 on 2023-04-20 14:01

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0020_populate_editable_url_names"),
    ]

    operations = [
        migrations.DeleteModel(
            name="BaseTemplate",
        ),
    ]
