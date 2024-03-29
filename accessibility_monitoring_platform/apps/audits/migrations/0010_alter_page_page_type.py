# Generated by Django 4.1a1 on 2022-06-23 07:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audits", "0009_audit_accessibility_statement_backup_url_date_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="page",
            name="page_type",
            field=models.CharField(
                choices=[
                    ("extra", "Additional"),
                    ("home", "Home"),
                    ("contact", "Contact"),
                    ("statement", "Accessibility statement"),
                    ("coronavirus", "Coronavirus"),
                    ("pdf", "PDF"),
                    ("form", "Form"),
                ],
                default="extra",
                max_length=20,
            ),
        ),
    ]
