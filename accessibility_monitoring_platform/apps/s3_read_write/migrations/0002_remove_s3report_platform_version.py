# Generated by Django 4.0.3 on 2022-04-20 10:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('s3_read_write', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='s3report',
            name='platform_version',
        ),
    ]
