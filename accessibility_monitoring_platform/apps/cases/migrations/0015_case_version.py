# Generated by Django 3.2.8 on 2021-10-22 13:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0014_auto_20211022_0851"),
    ]

    operations = [
        migrations.AddField(
            model_name="case",
            name="version",
            field=models.IntegerField(default=0),
        ),
    ]
