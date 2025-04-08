"""
Test forms of cases app
"""

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.db.models.query import QuerySet
from django.http import HttpResponse, StreamingHttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from ...cases.models import Case, CaseStatus
from ...common.models import Event
from ..models import Export, ExportCase
from .test_forms import CUTOFF_DATE, create_exportable_case

ORGANISATION_NAME: str = "Org Name"
COMPLIANCE_EMAIL_SENT_DATE: date = date(2024, 3, 18)
EXPORT_CSV_COLUMNS: str = "Equality body,Test type,Case number,Organisation"


def get_csv_streaming_content(
    response: StreamingHttpResponse,
) -> str:
    """Decode CSV HTTP response and break into column names and data"""
    content_chunks: list[str] = [
        chunk.decode("utf-8") for chunk in response.streaming_content
    ]
    content: str = "".join(content_chunks)
    return content


def create_cases_and_export(
    enforcement_body: Case.EnforcementBody = Case.EnforcementBody.EHRC,
) -> Export:
    """Creates cases and export"""
    case_1: Case = Case.objects.create(
        organisation_name=ORGANISATION_NAME,
        compliance_email_sent_date=COMPLIANCE_EMAIL_SENT_DATE,
        enforcement_body=enforcement_body,
    )
    case_2: Case = Case.objects.create(
        organisation_name="Other Org Name",
        compliance_email_sent_date=COMPLIANCE_EMAIL_SENT_DATE,
        enforcement_body=enforcement_body,
    )
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE cases_casestatus SET status = '{CaseStatus.Status.CASE_CLOSED_WAITING_TO_SEND}' WHERE id = {case_1.status.id}"
        )
        cursor.execute(
            f"UPDATE cases_casestatus SET status = '{CaseStatus.Status.CASE_CLOSED_WAITING_TO_SEND}' WHERE id = {case_2.status.id}"
        )

    user: User = User.objects.create()
    export: Export = Export.objects.create(
        cutoff_date=CUTOFF_DATE, exporter=user, enforcement_body=enforcement_body
    )
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
    assertContains(response, "EHRC")
    assertNotContains(response, "ECNI")

    response: HttpResponse = admin_client.get(
        f"{reverse(path_name)}?enforcement_body=ecni"
    )

    assert response.status_code == 200
    assertNotContains(response, "EHRC")
    assertContains(response, "ECNI")


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
def test_ehrc_export_page_loads(path_name, expected_content, admin_client):
    """Test that EHRC export-specific page view loads"""
    export: Export = create_cases_and_export()

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs={"pk": export.id})
    )

    assert response.status_code == 200
    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        (
            "exports:export-detail",
            '<h1 class="govuk-heading-xl">ECNI CSV export 20 March 2024</h1>',
        ),
        (
            "exports:export-confirm-delete",
            '<h1 class="govuk-heading-xl">Delete ECNI CSV export 20 March 2024</h1>',
        ),
        (
            "exports:export-confirm-export",
            '<h1 class="govuk-heading-xl">Confirm ECNI CSV export 20 March 2024</h1>',
        ),
    ],
)
def test_ecni_export_page_loads(path_name, expected_content, admin_client):
    """Test that ECNI export-specific page view loads"""
    export: Export = create_cases_and_export(enforcement_body=Case.EnforcementBody.ECNI)

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs={"pk": export.id})
    )

    assert response.status_code == 200
    assertContains(response, expected_content)


def test_draft_export_csv_returned(admin_client):
    """Test that draft csv returned"""
    export: Export = create_cases_and_export()

    response: StreamingHttpResponse = admin_client.get(
        reverse("exports:export-all-cases", kwargs={"pk": export.id})
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/csv"

    csv_response: str = get_csv_streaming_content(response=response)

    assert EXPORT_CSV_COLUMNS in csv_response
    assert ORGANISATION_NAME in csv_response


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


def test_all_export_cases_set_to_ready(admin_client):
    """Test that all export cases statuses are set to ready"""
    export: Export = create_cases_and_export()
    export_case_1: ExportCase = export.exportcase_set.first()
    export_case_2: ExportCase = export.exportcase_set.last()

    assert export_case_1.id != export_case_2.id
    assert export_case_1.status == ExportCase.Status.UNREADY
    assert export_case_2.status == ExportCase.Status.UNREADY

    response: HttpResponse = admin_client.get(
        reverse("exports:mark-all-cases-as-ready", kwargs={"pk": export.id})
    )

    assert response.status_code == 302
    assert response.url == reverse("exports:export-detail", kwargs={"pk": export.id})

    export_case_1_from_db: ExportCase = ExportCase.objects.get(id=export_case_1.id)
    export_case_2_from_db: ExportCase = ExportCase.objects.get(id=export_case_2.id)

    assert export_case_1_from_db.status == ExportCase.Status.READY
    assert export_case_2_from_db.status == ExportCase.Status.READY


def test_ready_export_csv_returned(admin_client):
    """
    Test that ready cases csv returned and contains only cases with
    ExportCase status of ready.
    """
    export: Export = create_cases_and_export()

    response: StreamingHttpResponse = admin_client.get(
        reverse("exports:export-ready-cases", kwargs={"pk": export.id})
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/csv"

    csv_response: str = get_csv_streaming_content(response=response)

    assert EXPORT_CSV_COLUMNS in csv_response
    assert ORGANISATION_NAME not in csv_response

    export_case: ExportCase = export.exportcase_set.first()
    export_case.status = ExportCase.Status.READY
    export_case.save()

    response: StreamingHttpResponse = admin_client.get(
        reverse("exports:export-ready-cases", kwargs={"pk": export.id})
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/csv"

    csv_response: str = get_csv_streaming_content(response=response)

    assert EXPORT_CSV_COLUMNS in csv_response
    assert ORGANISATION_NAME in csv_response


def test_create_export(admin_client, admin_user):
    """Test that export can be created"""
    create_exportable_case()

    response: HttpResponse = admin_client.post(
        reverse("exports:export-create"),
        {
            "enforcement_body": Case.EnforcementBody.EHRC,
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

    assert export.is_deleted is False

    response: HttpResponse = admin_client.post(
        reverse("exports:export-confirm-delete", kwargs={"pk": export.id}),
        {
            "is_deleted": "on",
            "delete": "Delete export",
        },
    )

    assert response.status_code == 302
    assert response.url == f'{reverse("exports:export-list")}?enforcement_body=ehrc'

    export_from_db: Export = Export.objects.get(id=export.id)

    assert export_from_db.is_deleted is True

    event: Event = Event.objects.all().first()

    assert event is not None
    assert event.parent == export


def test_export_case_as_email(admin_client):
    """
    Test that Case export can be rendered as a HTML table which can be copied into an
    email.
    """
    export: Export = create_cases_and_export(enforcement_body=Case.EnforcementBody.ECNI)
    case: ExportCase = export.exportcase_set.first()

    response: HttpResponse = admin_client.get(
        reverse(
            "exports:export-case-as-email",
            kwargs={"export_id": export.id, "pk": case.id},
        )
    )

    assert response.status_code == 200

    assertContains(
        response, '<tr><th scope="row">Equality body</th><td>ECNI</td></tr>', html=True
    )
