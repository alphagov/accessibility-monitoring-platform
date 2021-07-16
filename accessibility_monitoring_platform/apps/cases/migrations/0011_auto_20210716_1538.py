# Generated by Django 3.2.4 on 2021-07-16 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0010_case_enforcement_body_correspondance_notes'),
    ]

    operations = [
        migrations.RenameField(
            model_name='case',
            old_name='correspondance_notes',
            new_name='twelve_week_correspondance_notes',
        ),
        migrations.AddField(
            model_name='case',
            name='twelve_week_1_week_chaser_due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='twelve_week_1_week_chaser_sent_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='twelve_week_4_week_chaser_due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='twelve_week_4_week_chaser_sent_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='twelve_week_correspondance_acknowledged_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='twelve_week_update_requested_due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='twelve_week_update_requested_sent_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
