# Generated by Django 4.1.4 on 2023-03-13 10:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reminders", "0003_remove_reminder_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="reminder",
            name="updated",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
