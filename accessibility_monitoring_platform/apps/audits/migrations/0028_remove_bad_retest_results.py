"""
Retest check results should not have been created when the initial test result is not
an error.
"""

from django.db import migrations

REMOVE_BAD_RETEST_RESULTS: str = (
    "DELETE FROM audits_wcagcheckresultretest WHERE EXISTS (SELECT id FROM audits_wcagcheckresultinitial WHERE id = wcag_check_result_initial_id AND check_result_state <> 'error');"
)


class Migration(migrations.Migration):

    dependencies = [
        ("audits", "0027_create_statement_checks"),
    ]

    operations = [
        migrations.RunSQL(REMOVE_BAD_RETEST_RESULTS),
    ]
