# Generated by Django 4.1a1 on 2022-06-20 14:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0008_remove_reportwrapper_sub_header"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="reportwrapper",
            name="title_caption",
        ),
    ]
