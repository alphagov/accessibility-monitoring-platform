# Move second statement overview check to statement information page

from django.db import migrations

MOVE_ISSUE_NUMBERS: list[int] = [2, 44]
OLD_STATEMENT_CHECK_TYPE: str = "overview"
NEW_STATEMENT_CHECK_TYPE: str = "website"


def move_statement_questions(apps, schema_editor):
    StatementCheck = apps.get_model("audits", "StatementCheck")
    StatementCheckResult = apps.get_model("audits", "StatementCheckResult")
    RetestStatementCheckResult = apps.get_model("audits", "RetestStatementCheckResult")

    for issue_number in MOVE_ISSUE_NUMBERS:
        statement_check: StatementCheck = StatementCheck.objects.get(
            issue_number=issue_number
        )
        statement_check.type = NEW_STATEMENT_CHECK_TYPE
        statement_check.save()
        statement_check_results = StatementCheckResult.objects.filter(
            statement_check_id=statement_check.id
        )
        for statement_check_result in statement_check_results:
            statement_check_result.type = NEW_STATEMENT_CHECK_TYPE
        StatementCheckResult.objects.bulk_update(statement_check_results, ["type"])
        retest_statement_check_results = RetestStatementCheckResult.objects.filter(
            statement_check_id=statement_check.id
        )
        for retest_statement_check_result in retest_statement_check_results:
            retest_statement_check_result.type = NEW_STATEMENT_CHECK_TYPE
        RetestStatementCheckResult.objects.bulk_update(
            retest_statement_check_results, ["type"]
        )


def reverse_code(apps, schema_editor):
    StatementCheck = apps.get_model("audits", "StatementCheck")
    StatementCheckResult = apps.get_model("audits", "StatementCheckResult")
    RetestStatementCheckResult = apps.get_model("audits", "RetestStatementCheckResult")

    for issue_number in MOVE_ISSUE_NUMBERS:
        statement_check: StatementCheck = StatementCheck.objects.get(
            issue_number=issue_number
        )
        statement_check.type = OLD_STATEMENT_CHECK_TYPE
        statement_check.save()
        statement_check_results = StatementCheckResult.objects.filter(
            statement_check_id=statement_check.id
        )
        for statement_check_result in statement_check_results:
            statement_check_result.type = OLD_STATEMENT_CHECK_TYPE
        StatementCheckResult.objects.bulk_update(statement_check_results, ["type"])
        retest_statement_check_results = RetestStatementCheckResult.objects.filter(
            statement_check_id=statement_check.id
        )
        for retest_statement_check_result in retest_statement_check_results:
            retest_statement_check_result.type = OLD_STATEMENT_CHECK_TYPE
        RetestStatementCheckResult.objects.bulk_update(
            retest_statement_check_results, ["type"]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("audits", "0022_restore_old_statement_questions"),
    ]

    operations = [
        migrations.RunPython(move_statement_questions, reverse_code=reverse_code),
    ]
