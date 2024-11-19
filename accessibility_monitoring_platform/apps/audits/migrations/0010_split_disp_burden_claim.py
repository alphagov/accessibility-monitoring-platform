"""
    Disproportionate burden claim state includes a value for No claim
    or no statement (page). Record each part of that state separately.

    i.e. No claim and no statement should be separate choices available
    to the user.
"""

from enum import Enum

from django.db import migrations


class DisproportionateBurden(Enum):
    NO_ASSESSMENT: str = "no-assessment"
    ASSESSMENT: str = "assessment"
    NO_CLAIM: str = "no-claim"
    NO_STATEMENT: str = "no-statement"
    NOT_CHECKED: str = "not-checked"


def derive_no_claim_or_no_statement(audit, StatementPage) -> DisproportionateBurden:
    if StatementPage.objects.filter(audit=audit).count() > 0:
        return DisproportionateBurden.NO_CLAIM.value
    return DisproportionateBurden.NO_STATEMENT.value


def split_disproportionate_burden_claim(apps, schema_editor):
    Audit = apps.get_model("audits", "Audit")
    Retest = apps.get_model("audits", "Retest")
    StatementPage = apps.get_model("audits", "StatementPage")
    for audit in Audit.objects.filter(
        initial_disproportionate_burden_claim=DisproportionateBurden.NO_CLAIM.value
    ):
        audit.initial_disproportionate_burden_claim = derive_no_claim_or_no_statement(
            audit, StatementPage
        )
        audit.save()
    for audit in Audit.objects.filter(
        twelve_week_disproportionate_burden_claim=DisproportionateBurden.NO_CLAIM.value
    ):
        audit.twelve_week_disproportionate_burden_claim = (
            derive_no_claim_or_no_statement(audit, StatementPage)
        )
        audit.save()
    for retest in Retest.objects.filter(
        disproportionate_burden_claim=DisproportionateBurden.NO_CLAIM.value
    ):
        audit = Audit.objects.get(case=retest.case)
        retest.disproportionate_burden_claim = derive_no_claim_or_no_statement(
            audit, StatementPage
        )
        retest.save()


def reverse_code(apps, schema_editor):  # pylint: disable=unused-argument
    Audit = apps.get_model("audits", "Audit")
    Retest = apps.get_model("audits", "Retest")
    for audit in Audit.objects.filter(
        initial_disproportionate_burden_claim=DisproportionateBurden.NO_STATEMENT.value
    ):
        audit.initial_disproportionate_burden_claim = (
            DisproportionateBurden.NO_CLAIM.value
        )
        audit.save()
    for audit in Audit.objects.filter(
        twelve_week_disproportionate_burden_claim=DisproportionateBurden.NO_STATEMENT.value
    ):
        audit.twelve_week_disproportionate_burden_claim = (
            DisproportionateBurden.NO_CLAIM.value
        )
        audit.save()
    for retest in Retest.objects.filter(
        disproportionate_burden_claim=DisproportionateBurden.NO_STATEMENT.value
    ):
        retest.disproportionate_burden_claim = DisproportionateBurden.NO_CLAIM.value
        retest.save()


class Migration(migrations.Migration):

    dependencies = [
        (
            "audits",
            "0009_alter_audit_archive_audit_retest_disproportionate_burden_state_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            split_disproportionate_burden_claim, reverse_code=reverse_code
        ),
    ]
