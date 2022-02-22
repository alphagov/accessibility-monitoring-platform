# Generated by Django 4.0.2 on 2022-02-22 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audits', '0006_merge_0005_auto_20220201_1529_0005_auto_20220203_1546'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='audit',
            name='retest_of_audit',
        ),
        migrations.RemoveField(
            model_name='audit',
            name='type',
        ),
        migrations.AddField(
            model_name='audit',
            name='audit_retest_metadata_complete_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='audit',
            name='audit_retest_pages_complete_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='audit',
            name='audit_retest_statement_complete_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='audit',
            name='audit_retest_statement_decision_complete_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='audit',
            name='audit_retest_website_decision_complete_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='audit',
            name='retest_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='checkresult',
            name='retest_notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='checkresult',
            name='retest_state',
            field=models.CharField(choices=[('yes', 'Yes'), ('no', 'No'), ('partial', 'Partially'), ('not-applicable', 'N/A')], default='no', max_length=20),
        ),
        migrations.AddField(
            model_name='page',
            name='retest_complete_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='retest_page_missing_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
