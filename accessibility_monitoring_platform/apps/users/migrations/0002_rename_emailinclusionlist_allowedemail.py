# Generated by Django 4.1a1 on 2022-06-24 14:46

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="EmailInclusionList",
            new_name="AllowedEmail",
        ),
    ]
