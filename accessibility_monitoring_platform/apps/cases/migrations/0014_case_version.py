# Generated by Django 3.2.8 on 2021-10-21 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0013_alter_case_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='version',
            field=models.IntegerField(default=0),
        ),
    ]
