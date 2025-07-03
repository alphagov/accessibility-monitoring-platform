"""
Test forms of cases app
"""

from datetime import date

import pytest
from django.contrib.auth.models import User

from ...simplified.models import SimplifiedCase
from ..models import Export, ExportCase

ORGANISATION_NAME: str = "Org Name"
CUTOFF_DATE: date = date(2024, 2, 29)
COMPLIANCE_EMAIL_SENT_DATE: date = date(2024, 2, 28)


def create_cases_and_export() -> tuple[Export, SimplifiedCase]:
    """Creates cases and export"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME,
        compliance_email_sent_date=COMPLIANCE_EMAIL_SENT_DATE,
        status=SimplifiedCase.Status.CASE_CLOSED_WAITING_TO_SEND,
    )

    user: User = User.objects.create()
    export: Export = Export.objects.create(cutoff_date=CUTOFF_DATE, exporter=user)
    return export, simplified_case


def test_export_str():
    """Tests Export.__str__()"""

    export: Export = Export(cutoff_date=CUTOFF_DATE)

    assert str(export) == "EHRC CSV export 29 February 2024"


@pytest.mark.django_db
def test_export_save():
    """
    Tests Export.save() creates ExportCase objects for qualifying cases:

    * SimplifiedCase status is SimplifiedCase.Status.CASE_CLOSED_WAITING_TO_SEND
    * SimplifiedCase compliance_email_sent_date is less than or equal to Export.cutoff_date
    * SimplifiedCase enforcement body is EHRC
    """
    SimplifiedCase.objects.create()
    SimplifiedCase.objects.create(
        compliance_email_sent_date=COMPLIANCE_EMAIL_SENT_DATE,
        enforcement_body=SimplifiedCase.EnforcementBody.EHRC,
    )
    qualifying_case: SimplifiedCase = SimplifiedCase.objects.create(
        compliance_email_sent_date=COMPLIANCE_EMAIL_SENT_DATE,
        status=SimplifiedCase.Status.CASE_CLOSED_WAITING_TO_SEND,
    )

    user: User = User.objects.create()
    Export.objects.create(cutoff_date=CUTOFF_DATE, exporter=user)

    assert ExportCase.objects.all().count() == 1
    assert ExportCase.objects.all().first().simplified_case == qualifying_case


@pytest.mark.django_db
def test_export_save_excludes_ecni():
    """
    Tests Export.save() excludes cases for ECNI.
    """
    qualifying_case: SimplifiedCase = SimplifiedCase.objects.create(
        compliance_email_sent_date=COMPLIANCE_EMAIL_SENT_DATE,
        status=SimplifiedCase.Status.CASE_CLOSED_WAITING_TO_SEND,
    )

    user: User = User.objects.create()
    Export.objects.create(cutoff_date=CUTOFF_DATE, exporter=user)

    assert ExportCase.objects.all().count() == 1
    assert ExportCase.objects.all().first().simplified_case == qualifying_case

    qualifying_case.enforcement_body = SimplifiedCase.EnforcementBody.ECNI
    qualifying_case.save()

    Export.objects.create(cutoff_date=CUTOFF_DATE, exporter=user)

    assert ExportCase.objects.all().count() == 1  # No new ExportCase created


@pytest.mark.django_db
def test_export_save_excludes_complete_no_send():
    """
    Tests Export.save() excludes cases marked as not to be sent to equality body.
    """
    qualifying_case: SimplifiedCase = SimplifiedCase.objects.create(
        compliance_email_sent_date=COMPLIANCE_EMAIL_SENT_DATE,
        status=SimplifiedCase.Status.CASE_CLOSED_WAITING_TO_SEND,
    )

    user: User = User.objects.create()
    Export.objects.create(cutoff_date=CUTOFF_DATE, exporter=user)

    assert ExportCase.objects.all().count() == 1
    assert ExportCase.objects.all().first().simplified_case == qualifying_case

    qualifying_case.case_completed = SimplifiedCase.CaseCompleted.COMPLETE_NO_SEND
    qualifying_case.save()

    Export.objects.create(cutoff_date=CUTOFF_DATE, exporter=user)

    assert ExportCase.objects.all().count() == 1  # No new ExportCase created


@pytest.mark.django_db
def test_export_all_cases():
    """Tests Export.all_cases returns expected list of cases"""
    export, simplified_case = create_cases_and_export()

    assert export.all_cases == [simplified_case]


@pytest.mark.django_db
def test_export_ready_cases():
    """Tests Export.ready_cases returns expected list of cases"""
    export, simplified_case = create_cases_and_export()

    assert export.ready_cases == []

    export_case: ExportCase = export.exportcase_set.get(simplified_case=simplified_case)
    export_case.status = ExportCase.Status.READY
    export_case.save()

    assert export.ready_cases == [simplified_case]


@pytest.mark.django_db
def test_export_ready_cases_count():
    """Tests Export.ready_cases_count returns expected number"""
    export, simplified_case = create_cases_and_export()

    assert export.ready_cases_count == 0

    export_case: ExportCase = export.exportcase_set.get(simplified_case=simplified_case)
    export_case.status = ExportCase.Status.READY
    export_case.save()

    assert export.ready_cases_count == 1


@pytest.mark.django_db
def test_export_excluded_cases_count():
    """Tests Export.excluded_cases_count returns expected number"""
    export, simplified_case = create_cases_and_export()

    assert export.excluded_cases_count == 0

    export_case: ExportCase = export.exportcase_set.get(simplified_case=simplified_case)
    export_case.status = ExportCase.Status.EXCLUDED
    export_case.save()

    assert export.excluded_cases_count == 1


@pytest.mark.django_db
def test_export_unready_cases_count():
    """Tests Export.unready_cases_count returns expected number"""
    export, simplified_case = create_cases_and_export()

    assert export.unready_cases_count == 1

    export_case: ExportCase = export.exportcase_set.get(simplified_case=simplified_case)
    export_case.status = ExportCase.Status.READY
    export_case.save()

    assert export.unready_cases_count == 0


@pytest.mark.django_db
def test_export_case_str():
    """Tests ExportCase.__str__()"""
    export, simplified_case = create_cases_and_export()
    export_case: ExportCase = export.exportcase_set.get(simplified_case=simplified_case)

    assert (
        str(export_case)
        == f"EHRC CSV export 29 February 2024: {ORGANISATION_NAME} | #S-1"
    )
