"""
Test forms of cases app
"""

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from ...cases.models import Case, CaseStatus
from ...common.models import Event
from ..models import Export, ExportCase

ORGANISATION_NAME: str = "Org Name"
CUTOFF_DATE: date = date(2024, 3, 20)
COMPLIANCE_EMAIL_SENT_DATE: date = date(2024, 3, 18)
EXPORT_CSV_COLUMNS: str = "Equality body,Test type,Case number,Organisation"


def create_cases_and_export() -> Export:
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
    return export


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        (
            "exports:export-list",
            '<h1 class="govuk-heading-xl">EHRC CSV export manager</h1>',
        ),
        (
            "exports:export-create",
            '<h1 class="govuk-heading-xl">New EHRC CSV export</h1>',
        ),
    ],
)
def test_non_specific_export_page_loads(path_name, expected_content, admin_client):
    """Test that non-export-specific page view loads"""
    response: HttpResponse = admin_client.get(reverse(path_name))

    assert response.status_code == 200
    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        (
            "exports:export-detail",
            '<h1 class="govuk-heading-xl">EHRC CSV export 20 March 2024</h1>',
        ),
        (
            "exports:export-confirm-delete",
            '<h1 class="govuk-heading-xl">Delete EHRC CSV export 20 March 2024</h1>',
        ),
        (
            "exports:export-confirm-export",
            '<h1 class="govuk-heading-xl">Confirm EHRC CSV export 20 March 2024</h1>',
        ),
    ],
)
def test_export_page_loads(path_name, expected_content, admin_client):
    """Test that export-specific page view loads"""
    export: Export = create_cases_and_export()

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs={"pk": export.id})
    )

    assert response.status_code == 200
    assertContains(response, expected_content)


def test_draft_export_csv_returned(admin_client):
    """Test that draft csv returned"""
    export: Export = create_cases_and_export()

    response: HttpResponse = admin_client.get(
        reverse("exports:export-all-cases", kwargs={"pk": export.id})
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/csv"
    assertContains(response, EXPORT_CSV_COLUMNS)
    assertContains(response, ORGANISATION_NAME)


@pytest.mark.parametrize(
    "path_name, expected_status",
    [
        (
            "exports:case-mark-as-ready",
            ExportCase.Status.READY,
        ),
        (
            "exports:case-mark-as-excluded",
            ExportCase.Status.EXCLUDED,
        ),
        (
            "exports:case-mark-as-unready",
            ExportCase.Status.UNREADY,
        ),
    ],
)
def test_export_case_status_updated(path_name, expected_status, admin_client):
    """Test that ExportCase.status is updated"""
    export: Export = create_cases_and_export()
    export_case: ExportCase = export.exportcase_set.first()

    if expected_status == ExportCase.Status.UNREADY:
        export_case.status = ExportCase.Status.EXCLUDED
        export_case.save()

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs={"pk": export_case.id})
    )

    assert response.status_code == 302

    export_case_from_db: ExportCase = ExportCase.objects.get(id=export_case.id)

    assert export_case_from_db.status == expected_status


def test_ready_export_csv_returned(admin_client):
    """
    Test that ready cases csv returned and contains only cases with
    ExportCase status of ready.
    """
    export: Export = create_cases_and_export()

    response: HttpResponse = admin_client.get(
        reverse("exports:export-ready-cases", kwargs={"pk": export.id})
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/csv"
    assertContains(response, EXPORT_CSV_COLUMNS)
    assertNotContains(response, ORGANISATION_NAME)

    export_case: ExportCase = export.exportcase_set.first()
    export_case.status = ExportCase.Status.READY
    export_case.save()

    response: HttpResponse = admin_client.get(
        reverse("exports:export-ready-cases", kwargs={"pk": export.id})
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/csv"
    assertContains(response, EXPORT_CSV_COLUMNS)
    assertContains(response, ORGANISATION_NAME)


def test_create_export(admin_client, admin_user):
    """Test that export can be created"""

    response: HttpResponse = admin_client.post(
        reverse("exports:export-create"),
        {
            "cutoff_date_0": CUTOFF_DATE.day,
            "cutoff_date_1": CUTOFF_DATE.month,
            "cutoff_date_2": CUTOFF_DATE.year,
            "save": "Create",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("exports:export-detail", kwargs={"pk": 1})

    export: Export = Export.objects.get(id=1)

    assert export.cutoff_date == CUTOFF_DATE
    assert export.exporter is not None
    assert export.exporter == admin_user

    event: Event = Event.objects.all().first()

    assert event is not None
    assert event.parent == export
    assert event.type == "model_create"


def test_confirm_export(admin_client):
    """
    Test that export can be confirmed. Bulk update happens and user is
    redirected to CSV.
    """
    export: Export = create_cases_and_export()
    export_case: ExportCase = export.exportcase_set.first()
    export_case.status = ExportCase.Status.READY
    export_case.save()

    assert export_case.case.sent_to_enforcement_body_sent_date is None

    response: HttpResponse = admin_client.post(
        reverse("exports:export-confirm-export", kwargs={"pk": export.id}),
        {
            "cutoff_date": "2024-03-21",
            "submit": "Export and update all ready cases",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "exports:export-ready-cases", kwargs={"pk": export.id}
    )

    case: Case = Case.objects.get(id=export_case.case.id)

    assert case.sent_to_enforcement_body_sent_date == date.today()

    events: QuerySet[Event] = Event.objects.all()

    assert len(events) == 2
    assert events[0].parent == export
    assert events[0].type == "model_update"
    assert events[1].parent == case
    assert events[1].type == "model_update"


def test_confirm_delete_export(admin_client):
    """Test that export can be deleted"""
    export: Export = create_cases_and_export()

    assert export.is_deleted == False

    response: HttpResponse = admin_client.post(
        reverse("exports:export-confirm-delete", kwargs={"pk": export.id}),
        {
            "is_deleted": "on",
            "delete": "Delete export",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("exports:export-list")

    export_from_db: Export = Export.objects.get(id=export.id)

    assert export_from_db.is_deleted is True

    event: Event = Event.objects.all().first()

    assert event is not None
    assert event.parent == export
    assert event.type == "model_update"
