# Generated by Django 4.1b1 on 2022-07-14 12:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0009_remove_reportwrapper_title_caption"),
    ]

    operations = [
        migrations.AlterField(
            model_name="basetemplate",
            name="template_type",
            field=models.CharField(
                choices=[
                    ("markdown", "Markdown"),
                    ("urls", "Contains URL table"),
                    ("issues-intro", "Markdown issues intro"),
                    ("issues", "Contains Issues table"),
                    ("html", "HTML"),
                ],
                default="markdown",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="section",
            name="template_type",
            field=models.CharField(
                choices=[
                    ("markdown", "Markdown"),
                    ("urls", "Contains URL table"),
                    ("issues-intro", "Markdown issues intro"),
                    ("issues", "Contains Issues table"),
                    ("html", "HTML"),
                ],
                default="markdown",
                max_length=20,
            ),
        ),
    ]
