# Generated by Django 4.1.1 on 2022-09-28 12:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("comments", "0004_rename_comments_comment_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="path",
            field=models.TextField(default=""),
        ),
    ]
