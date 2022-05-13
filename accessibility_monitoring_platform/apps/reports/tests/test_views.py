"""
Tests for reports views
"""
import pytest
from typing import Dict

from moto import mock_s3

from pytest_django.asserts import assertContains, assertNotContains

from django.http import HttpResponse
from django.urls import reverse

from ...audits.models import Audit
from ...cases.models import Case, REPORT_APPROVED_STATUS_APPROVED
from ...s3_read_write.models import S3Report

from ..models import Report, TableRow, Section
from ..utils import (
    DELETE_ROW_BUTTON_PREFIX,
    UNDELETE_ROW_BUTTON_PREFIX,
    MOVE_ROW_UP_BUTTON_PREFIX,
    MOVE_ROW_DOWN_BUTTON_PREFIX,
)

SECTION_NAME: str = "Section name"
SECTION_CONTENT: str = "I am section content"


def create_report() -> Report:
    """Create a report"""
    case: Case = Case.objects.create()
    Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)
    return report


def create_section(report: Report) -> Section:
    """Create section in report"""
    return Section.objects.create(
        report=report, name=SECTION_NAME, content=SECTION_CONTENT, position=1
    )


def test_create_report_redirects(admin_client):
    """Test that report create redirects to report metadata"""
    case: Case = Case.objects.create()
    path_kwargs: Dict[str, int] = {"case_id": case.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse("reports:report-create", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse("reports:report-publisher", kwargs={"pk": 1})  # type: ignore


def test_rebuild_report_redirects(admin_client):
    """Test that report rebuild redirects to report details"""
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse("reports:report-rebuild", kwargs=report_pk_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse("reports:report-detail", kwargs=report_pk_kwargs)  # type: ignore


@mock_s3
def test_publish_report_redirects(admin_client):
    """
    Test that report publish redirects to report details
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore
    number_of_s3_reports: int = S3Report.objects.filter(case=report.case).count()

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publish", kwargs=report_pk_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse("reports:report-publisher", kwargs=report_pk_kwargs)  # type: ignore
    assert S3Report.objects.filter(case=report.case).count() == number_of_s3_reports + 1


@mock_s3
def test_report_published_message_shown(admin_client):
    """Test publishing the report causes a message to be shown on the next page"""
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publish", kwargs=report_pk_kwargs), follow=True
    )

    assert response.status_code == 200

    assertContains(
        response,
        """<div class="govuk-inset-text">HTML report successfully created!</div>""",
        html=True,
    )


@pytest.mark.parametrize(
    "path_name, expected_header",
    [
        ("reports:report-detail", ">Edit report</h1>"),
        ("reports:edit-report-metadata", ">Report metadata</h1>"),
        ("reports:s3-report-list", ">Report versions</h1>"),
        ("reports:report-publisher", f"<p>{SECTION_CONTENT}</p>"),
        (
            "reports:report-confirm-refresh",
            ">Are you sure you want to refresh the report?</h1>",
        ),
        (
            "reports:report-confirm-publish",
            "Unable to publish report without QA approval",
        ),
    ],
)
def test_report_specific_page_loads(path_name, expected_header, admin_client):
    """Test that the report-specific page loads"""
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore
    create_section(report)

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, expected_header)


def test_report_details_page_shows_notification(admin_client):
    """
    Test that the report details page shows a notification advising user to
    mark report as ready to review
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore
    create_section(report)

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(
        response,
        "If this report is ready to be reviewed, mark 'Report ready to be reviewed' in QA process.",
    )


def test_section_edit_page_loads(admin_client):
    """Test that the edit section page loads"""
    report: Report = create_report()
    section: Section = create_section(report)
    section_pk_kwargs: Dict[str, int] = {"pk": section.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse("reports:edit-report-section", kwargs=section_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, section.name)


@pytest.mark.django_db
def test_report_edit_metadata_save_stays_on_page(admin_client):
    """
    Test that pressing the save button on report edit metadata stays on the same page
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore
    url: str = reverse("reports:edit-report-metadata", kwargs=report_pk_kwargs)

    response: HttpResponse = admin_client.post(
        url,
        {
            "version": report.version,
            "save": "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == url  # type: ignore


@pytest.mark.django_db
def test_report_edit_metadata_redirects_to_details(admin_client):
    """Test that report edit metadata redirects to report details on save"""
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore
    url: str = reverse("reports:edit-report-metadata", kwargs=report_pk_kwargs)

    response: HttpResponse = admin_client.post(
        url,
        {
            "version": report.version,
            "save_exit": "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("reports:report-detail", kwargs=report_pk_kwargs)  # type: ignore


@pytest.mark.django_db
def test_report_edit_section_save_button_stays_on_page(admin_client):
    """Test pressing save button on report edit section stays on page"""
    report: Report = create_report()
    section: Section = create_section(report)
    section_pk_kwargs: Dict[str, int] = {"pk": section.id}  # type: ignore
    url: str = reverse("reports:edit-report-section", kwargs=section_pk_kwargs)

    response: HttpResponse = admin_client.post(
        url,
        {
            "version": section.version,
            "template_type": "markdown",
            "save": "Button value",
            "form-TOTAL_FORMS": 0,
            "form-INITIAL_FORMS": 0,
            "form-MIN_NUM_FORMS": 0,
            "form-MAX_NUM_FORMS": 1000,
        },
    )

    assert response.status_code == 302
    assert response.url == url  # type: ignore


@pytest.mark.django_db
def test_report_edit_section_redirects_to_details(admin_client):
    """Test that report edit section redirects to report details on save"""
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore
    section: Section = create_section(report)
    section_pk_kwargs: Dict[str, int] = {"pk": section.id}  # type: ignore
    url: str = reverse("reports:edit-report-section", kwargs=section_pk_kwargs)

    response: HttpResponse = admin_client.post(
        url,
        {
            "version": section.version,
            "template_type": "markdown",
            "save_exit": "Button value",
            "form-TOTAL_FORMS": 0,
            "form-INITIAL_FORMS": 0,
            "form-MIN_NUM_FORMS": 0,
            "form-MAX_NUM_FORMS": 1000,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("reports:report-detail", kwargs=report_pk_kwargs)  # type: ignore


@pytest.mark.parametrize(
    "button_prefix",
    [
        DELETE_ROW_BUTTON_PREFIX,
        UNDELETE_ROW_BUTTON_PREFIX,
        MOVE_ROW_UP_BUTTON_PREFIX,
        MOVE_ROW_DOWN_BUTTON_PREFIX,
    ],
)
@pytest.mark.django_db
def test_report_edit_section_stays_on_page_on_row_button_pressed(
    button_prefix, admin_client
):
    """Test that report edit section stays on page when row-related button pressed"""
    report: Report = create_report()
    section: Section = create_section(report)
    section_pk_kwargs: Dict[str, int] = {"pk": section.id}  # type: ignore
    table_row: TableRow = TableRow.objects.create(section=section, row_number=1)
    table_row_id: int = table_row.id  # type: ignore
    url: str = reverse("reports:edit-report-section", kwargs=section_pk_kwargs)

    response: HttpResponse = admin_client.post(
        url,
        {
            "version": section.version,
            "template_type": "markdown",
            f"{button_prefix}{table_row_id}": "Button value",
            "form-TOTAL_FORMS": 0,
            "form-INITIAL_FORMS": 0,
            "form-MIN_NUM_FORMS": 0,
            "form-MAX_NUM_FORMS": 1000,
        },
    )

    assert response.status_code == 302
    assert response.url == f"{url}#row-{table_row_id}"  # type: ignore


def test_unapproved_report_confirm_publish_asks_for_approval(admin_client):
    """
    Test that the confirm publish page asks for report to be QA approved
    when it has not been.
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse("reports:report-confirm-publish", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200
    assertContains(response, "Unable to publish report without QA approval")
    assertContains(response, "Have the report approved by another auditor")
    assertNotContains(response, "Create HTML report")


def test_approved_report_confirm_publish_does_not_ask_for_approval(admin_client):
    """
    Test that the confirm publish page does not ask for report to be QA approved
    if it is already approved
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore
    case: Case = report.case  # type: ignore
    case.report_approved_status = REPORT_APPROVED_STATUS_APPROVED
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("reports:report-confirm-publish", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200
    assertContains(response, "Are you sure you want to create a HTML report?")
    assertNotContains(response, "Have the report approved by another auditor")
    assertContains(response, "Create HTML report")


def test_edit_report_wrapper_page_loads(admin_client):
    """Test that the edit report wrapper page loads"""
    response: HttpResponse = admin_client.get(reverse("reports:edit-report-wrapper"))

    assert response.status_code == 200

    assertContains(response, ">Report viewer editor</h1>")
