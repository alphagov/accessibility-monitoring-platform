# Generated by Django 5.0.4 on 2024-06-05 08:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("cases", "0001_initial"),
        ("common", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="case",
            name="sector",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="common.sector",
            ),
        ),
        migrations.AddField(
            model_name="case",
            name="subcategory",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="common.subcategory",
            ),
        ),
        migrations.AddField(
            model_name="casecompliance",
            name="case",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="compliance",
                to="cases.case",
            ),
        ),
        migrations.AddField(
            model_name="caseevent",
            name="case",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="cases.case"
            ),
        ),
        migrations.AddField(
            model_name="caseevent",
            name="done_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="case_event_done_by_user",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="casestatus",
            name="case",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="status",
                to="cases.case",
            ),
        ),
        migrations.AddField(
            model_name="contact",
            name="case",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="cases.case"
            ),
        ),
        migrations.AddField(
            model_name="equalitybodycorrespondence",
            name="case",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="cases.case"
            ),
        ),
        migrations.AddField(
            model_name="zendeskticket",
            name="case",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="cases.case"
            ),
        ),
    ]
