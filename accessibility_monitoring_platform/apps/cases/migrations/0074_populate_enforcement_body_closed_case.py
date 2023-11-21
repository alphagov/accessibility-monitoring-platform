"""Populate new Case fields enforcement_body_closed_case and variant"""
from django.db import migrations


def populate_enforcement_body_closed_case(
    apps, schema_editor
):  # pylint: disable=unused-argument
    """
    Mapping rules:

    Yes (Equality body pursuing this case?) -> Yes (Enforcement body has officially closed the case?)
    Yes, in progress (Equality body pursuing this case?) -> Case in progress (Enforcement body has officially closed the case?)
    No (Equality body pursuing this case?) -> No (or holding) (Enforcement body has officially closed the case?)

    case.enforcement_body_pursuing -> case.enforcement_body_closed_case
    ("yes-completed", "Yes, completed"), -> ("yes", "Yes")
    ("yes-in-progress", "Yes, in progress"), -> ("in-progress", "Case in progress")
    ("no", "No"), -> ("no", "No (or holding)")
    """
    Case = apps.get_model("cases", "Case")
    Audit = apps.get_model("audits", "Audit")
    StatementCheckResult = apps.get_model("audits", "StatementCheckResult")
    Report = apps.get_model("reports", "Report")
    for case in Case.objects.all():
        if case.enforcement_body_pursuing == "yes-completed":
            case.enforcement_body_closed_case = "yes"
        elif case.enforcement_body_pursuing == "yes-in-progress":
            case.enforcement_body_closed_case = "in-progress"
        else:
            case.enforcement_body_closed_case = "no"

        if Audit.objects.filter(case=case).count() == 0:
            case.variant = "archived"
        else:
            audit = Audit.objects.get(case=case)
            if StatementCheckResult.objects.filter(audit=audit).count() > 0:
                case.variant = "statement-content"
            elif Report.objects.filter(case=case).count() > 0:
                case.variant = "reporting"
            else:
                case.variant = "archived"

        case.save()


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0073_remove_contact_created_by_and_more"),
    ]

    operations = [
        migrations.RunPython(
            populate_enforcement_body_closed_case, reverse_code=reverse_code
        ),
    ]
