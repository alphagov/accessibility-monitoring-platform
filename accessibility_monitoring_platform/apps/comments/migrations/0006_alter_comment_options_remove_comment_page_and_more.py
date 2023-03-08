# Generated by Django 4.1.4 on 2023-02-23 10:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("comments", "0005_alter_comment_path"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="comment",
            options={"ordering": ["created_date"]},
        ),
        migrations.RemoveField(
            model_name="comment",
            name="page",
        ),
        migrations.RemoveField(
            model_name="comment",
            name="path",
        ),
    ]