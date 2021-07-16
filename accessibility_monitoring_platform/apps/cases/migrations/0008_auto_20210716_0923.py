# Generated by Django 3.2.4 on 2021-07-16 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0007_case_correspondance_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='archive_notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='case',
            name='archive_reason',
            field=models.CharField(choices=[('not-psb', 'Organisation is not a public sector body'), ('mistake', 'Case was opened by mistake'), ('duplicate', 'This case was a duplicate case'), ('other', 'Other')], default='unknown', max_length=200),
        ),
    ]
