# Generated by Django 4.1.4 on 2023-02-24 09:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("comments", "0007_comment_history_events"),
    ]

    operations = [
        migrations.DeleteModel(
            name="CommentHistory",
        ),
    ]
