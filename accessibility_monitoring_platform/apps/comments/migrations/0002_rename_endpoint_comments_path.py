# Generated by Django 3.2.7 on 2021-09-30 16:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("comments", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="comments",
            old_name="endpoint",
            new_name="path",
        ),
    ]
