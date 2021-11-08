# Generated by Django 3.2.8 on 2021-11-08 16:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0017_remove_case_service_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='testing_methodology',
            field=models.CharField(choices=[('platform', 'Platform'), ('spreadsheet', 'Testing spreadsheet')], default='spreadsheet', max_length=20),
        ),
    ]
