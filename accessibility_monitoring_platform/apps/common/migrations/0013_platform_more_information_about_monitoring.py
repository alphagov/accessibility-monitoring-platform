# Generated by Django 4.1 on 2022-09-12 14:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0012_platform_markdown_cheatsheet"),
    ]

    operations = [
        migrations.AddField(
            model_name="platform",
            name="more_information_about_monitoring",
            field=models.TextField(
                blank=True,
                default="# More Information\n\nMore information about monitoring placeholder",
            ),
        ),
    ]
