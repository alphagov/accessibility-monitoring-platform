# Generated by Django 3.2.11 on 2022-02-01 15:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0022_auto_20220127_1444"),
    ]

    operations = [
        migrations.RenameField(
            model_name="case",
            old_name="final_decision_complete_date",
            new_name="case_close_complete_date",
        ),
        migrations.AddField(
            model_name="case",
            name="final_statement_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="case",
            name="final_website_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="case",
            name="is_ready_for_final_decision",
            field=models.CharField(
                choices=[("yes", "Yes"), ("no", "No")], default="no", max_length=20
            ),
        ),
        migrations.AddField(
            model_name="case",
            name="review_changes_complete_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="case",
            name="website_state_final",
            field=models.CharField(
                choices=[
                    ("compliant", "Compliant"),
                    ("partially-compliant", "Partially compliant"),
                    ("not-known", "Not known"),
                ],
                default="not-known",
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name="case",
            name="website_state_notes_final",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="case",
            name="case_completed",
            field=models.CharField(
                choices=[
                    (
                        "complete-send",
                        "Case is complete and is ready to send to the equality body",
                    ),
                    (
                        "complete-no-send",
                        "Case should not be sent to the equality body",
                    ),
                    ("no-decision", "Case still in progress"),
                ],
                default="no-decision",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="case",
            name="is_complaint",
            field=models.CharField(
                choices=[("yes", "Yes"), ("no", "No")], default="no", max_length=20
            ),
        ),
        migrations.AlterField(
            model_name="case",
            name="is_disproportionate_claimed",
            field=models.CharField(
                choices=[("yes", "Yes"), ("no", "No"), ("unknown", "Not known")],
                default="unknown",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="case",
            name="no_psb_contact",
            field=models.CharField(
                choices=[("yes", "Yes"), ("no", "No")], default="no", max_length=20
            ),
        ),
    ]
