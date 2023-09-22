# Generated by Django 4.2.4 on 2023-09-22 14:27

from django.db import migrations

FIRST_STATEMENT_CONTENT_CASE_ID: int = 1170


def populate_accessibility_statement_states(
    apps, schema_editor
):  # pylint: disable=unused-argument
    Case = apps.get_model("cases", "Case")
    Audit = apps.get_model("audits", "Audit")
    StatementCheckResult = apps.get_model("audits", "StatementCheckResult")
    Page = apps.get_model("audits", "Page")
    for case in Case.objects.filter(id__gte=FIRST_STATEMENT_CONTENT_CASE_ID):
        audit = Audit.objects.filter(case=case).first()
        if audit:
            statement_page = Page.objects.filter(
                audit=audit, page_type="statement"
            ).first()
            failed_statement_checks = StatementCheckResult.objects.filter(
                audit=audit, check_result_state="no"
            )
            failed_statement_retests = StatementCheckResult.objects.filter(
                audit=audit, retest_state="no"
            )

            if statement_page or case.twelve_week_accessibility_statement_url:
                if failed_statement_checks:
                    case.accessibility_statement_state = "not-compliant"
                else:
                    case.accessibility_statement_state = "compliant"
                if failed_statement_retests:
                    case.accessibility_statement_state_final = "not-compliant"
                else:
                    case.accessibility_statement_state_final = "compliant"
            else:
                case.accessibility_statement_state = "not-compliant"
                case.accessibility_statement_state_final = "not-compliant"
            case.save()


def reset_accessibility_statement_states(
    apps, schema_editor
):  # pylint: disable=unused-argument
    Case = apps.get_model("cases", "Case")
    Audit = apps.get_model("audits", "Audit")
    for case in Case.objects.filter(id__gte=FIRST_STATEMENT_CONTENT_CASE_ID):
        audit = Audit.objects.filter(case=case).first()
        if audit:
            case.accessibility_statement_state = "unknown"
            case.accessibility_statement_state_final = "unknown"
            case.save()


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0062_remove_contact_notes"),
    ]

    operations = [
        migrations.RunPython(
            populate_accessibility_statement_states,
            reverse_code=reset_accessibility_statement_states,
        ),
    ]
