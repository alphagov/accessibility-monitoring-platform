"""
Test forms of cases app
"""

from datetime import date
from typing import Tuple

import pytest
from django.contrib.auth.models import User
from django.db import connection

from ...cases.models import Case, CaseStatus
from ..models import Export, ExportCase

ORGANISATION_NAME: str = "Org Name"
CUTOFF_DATE: date = date(2024, 2, 29)
COMPLIANCE_EMAIL_SENT_DATE: date = date(2024, 2, 28)


def create_cases_and_export() -> Tuple[Export, Case]:
    """Creates cases and export"""
    case: Case = Case.objects.create(
        organisation_name=ORGANISATION_NAME,
        compliance_email_sent_date=COMPLIANCE_EMAIL_SENT_DATE,
    )
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE cases_casestatus SET status = '{CaseStatus.Status.CASE_CLOSED_WAITING_TO_SEND}' WHERE id = {case.status.id}"
        )

    user: User = User.objects.create()
    export: Export = Export.objects.create(cutoff_date=CUTOFF_DATE, exporter=user)
    return export, case


def test_export_str():
    """Tests Export.__str__()"""

    export: Export = Export(cutoff_date=CUTOFF_DATE)

    assert str(export) == "EHRC CSV export 29 February 2024"


@pytest.mark.django_db
def test_export_save():
    """Tests Export.save() creates ExportCase objects for qualifying cases"""
    Case.objects.create()
    Case.objects.create(compliance_email_sent_date=COMPLIANCE_EMAIL_SENT_DATE)
    qualifying_case: Case = Case.objects.create(
        compliance_email_sent_date=COMPLIANCE_EMAIL_SENT_DATE
    )
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE cases_casestatus SET status = '{CaseStatus.Status.CASE_CLOSED_WAITING_TO_SEND}' WHERE id = {qualifying_case.status.id}"
        )

    user: User = User.objects.create()
    Export.objects.create(cutoff_date=CUTOFF_DATE, exporter=user)

    assert ExportCase.objects.all().count() == 1
    assert ExportCase.objects.all().first().case == qualifying_case


@pytest.mark.django_db
def test_export_all_cases():
    """Tests Export.all_cases returns expected list of cases"""
    export, case = create_cases_and_export()

    assert export.all_cases == [case]


@pytest.mark.django_db
def test_export_ready_cases():
    """Tests Export.ready_cases returns expected list of cases"""
    export, case = create_cases_and_export()

    assert export.ready_cases == []

    export_case: ExportCase = export.exportcase_set.get(case=case)
    export_case.status = ExportCase.Status.READY
    export_case.save()

    assert export.ready_cases == [case]


@pytest.mark.django_db
def test_export_ready_cases_count():
    """Tests Export.ready_cases_count returns expected number"""
    export, case = create_cases_and_export()

    assert export.ready_cases_count == 0

    export_case: ExportCase = export.exportcase_set.get(case=case)
    export_case.status = ExportCase.Status.READY
    export_case.save()

    assert export.ready_cases_count == 1


@pytest.mark.django_db
def test_export_excluded_cases_count():
    """Tests Export.excluded_cases_count returns expected number"""
    export, case = create_cases_and_export()

    assert export.excluded_cases_count == 0

    export_case: ExportCase = export.exportcase_set.get(case=case)
    export_case.status = ExportCase.Status.EXCLUDED
    export_case.save()

    assert export.excluded_cases_count == 1


@pytest.mark.django_db
def test_export_unready_cases_count():
    """Tests Export.unready_cases_count returns expected number"""
    export, case = create_cases_and_export()

    assert export.unready_cases_count == 1

    export_case: ExportCase = export.exportcase_set.get(case=case)
    export_case.status = ExportCase.Status.READY
    export_case.save()

    assert export.unready_cases_count == 0


@pytest.mark.django_db
def test_export_case_str():
    """Tests ExportCase.__str__()"""
    export, case = create_cases_and_export()
    export_case: ExportCase = export.exportcase_set.get(case=case)

    assert (
        str(export_case)
        == f"EHRC CSV export 29 February 2024: {ORGANISATION_NAME} | #1"
    )
