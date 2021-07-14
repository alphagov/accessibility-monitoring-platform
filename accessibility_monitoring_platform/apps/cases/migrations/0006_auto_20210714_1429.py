# Generated by Django 3.2.4 on 2021-07-14 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0005_auto_20210708_1017'),
    ]

    operations = [
        migrations.RenameField(
            model_name='case',
            old_name='week_12_followup_date',
            new_name='report_followup_week_12_due_date',
        ),
        migrations.RenameField(
            model_name='case',
            old_name='week_12_followup_email_sent_date',
            new_name='report_followup_week_12_sent_date',
        ),
        migrations.RemoveField(
            model_name='case',
            name='week_12_followup_email_acknowledgement_date',
        ),
        migrations.AddField(
            model_name='case',
            name='report_followup_week_1_due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='report_followup_week_1_sent_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='report_followup_week_4_due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='report_followup_week_4_sent_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='report_followup_week_7_due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='report_followup_week_7_sent_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
