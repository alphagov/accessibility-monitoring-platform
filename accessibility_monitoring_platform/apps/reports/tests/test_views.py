"""
Tests for reports views
"""
import pytest
from typing import Dict

from moto import mock_s3

from pytest_django.asserts import assertContains

from django.http import HttpResponse
from django.urls import reverse

from ...audits.models import Audit
from ...cases.models import Case

from ..models import Report, PublishedReport, TableRow, Section
from ..utils import (
    DELETE_ROW_BUTTON_PREFIX,
    UNDELETE_ROW_BUTTON_PREFIX,
    MOVE_ROW_UP_BUTTON_PREFIX,
    MOVE_ROW_DOWN_BUTTON_PREFIX,
)

SECTION_NAME: str = "Section name"
SECTION_CONTENT: str = "I am section content"
PUBLISHED_REPORT_HTML: str = "<p>I am a published report</p>"


def create_report() -> Report:
    """Create a report"""
    case: Case = Case.objects.create()
    Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)
    PublishedReport.objects.create(report=report, html_content=PUBLISHED_REPORT_HTML)
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

    assert response.url == reverse("reports:report-detail", kwargs={"pk": 1})


def test_rebuild_report_redirects(admin_client):
    """Test that report rebuild redirects to report details"""
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse("reports:report-rebuild", kwargs=report_pk_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse("reports:report-detail", kwargs=report_pk_kwargs)


@mock_s3
def test_publish_report_redirects(admin_client):
    """
    Test that report publish creates a PublishedReport object and
    redirects to report details
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore
    number_of_published_reports: int = PublishedReport.objects.filter(
        report=report
    ).count()

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publish", kwargs=report_pk_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse("reports:report-detail", kwargs=report_pk_kwargs)
    assert (
        PublishedReport.objects.filter(report=report).count()
        == number_of_published_reports + 1
    )


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
        ("reports:report-detail", ">View report</h1>"),
        ("reports:edit-report-metadata", ">Report metadata</h1>"),
        ("reports:published-report-list", ">Report versions</h1>"),
        ("reports:report-preview", f"<p>{SECTION_CONTENT}</p>"),
        (
            "reports:report-confirm-rebuild",
            ">Are you sure you want to rebuild the report?</h1>",
        ),
        (
            "reports:report-confirm-publish",
            ">Are you sure you want to create a HTML report?</h1>",
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


def test_published_report_detail_page_loads(admin_client):
    """Test that the published report detail page loads"""
    report: Report = create_report()
    published_report: PublishedReport = report.publishedreport_set.first()  # type: ignore
    published_report_pk_kwargs: Dict[str, int] = {"pk": published_report.id}  # type: ignore
    create_section(report)

    response: HttpResponse = admin_client.get(
        reverse("reports:published-report-detail", kwargs=published_report_pk_kwargs)
    )

    assert response.status_code == 200
    assertContains(response, PUBLISHED_REPORT_HTML)


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
    assert response.url == url


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
    assert response.url == reverse("reports:report-detail", kwargs=report_pk_kwargs)


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
    assert response.url == url


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
    assert response.url == reverse("reports:report-detail", kwargs=report_pk_kwargs)


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
    assert response.url == f"{url}#row-{table_row_id}"
