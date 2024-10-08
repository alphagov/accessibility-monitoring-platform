# Generated by Django 5.0.7 on 2024-08-15 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0004_case_no_contact_four_week_chaser_due_date_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="case",
            old_name="contact_details_complete_date",
            new_name="manage_contact_details_complete_date",
        ),
        migrations.RenameField(
            model_name="case",
            old_name="find_contact_details_complete_date",
            new_name="request_contact_details_complete_date",
        ),
        migrations.AddField(
            model_name="case",
            name="enable_correspondence_process",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="case",
            name="four_week_contact_details_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="case",
            name="no_psb_contact_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="case",
            name="one_week_contact_details_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="contact",
            name="version",
            field=models.IntegerField(default=0),
        ),
    ]
