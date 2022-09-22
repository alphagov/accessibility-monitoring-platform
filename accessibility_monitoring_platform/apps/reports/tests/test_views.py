"""
Tests for reports views
"""
import pytest
from typing import Dict
from datetime import timedelta

from moto import mock_s3

from pytest_django.asserts import assertContains, assertNotContains

from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from ...audits.models import (
    Audit,
)
from ...cases.models import (
    Case,
    REPORT_APPROVED_STATUS_APPROVED,
    REPORT_READY_TO_REVIEW,
)
from ...s3_read_write.models import S3Report

from ..models import Report, TableRow, Section, ReportVisitsMetrics, TEMPLATE_TYPE_ISSUES_TABLE
from ..utils import (
    DELETE_ROW_BUTTON_PREFIX,
    UNDELETE_ROW_BUTTON_PREFIX,
    MOVE_ROW_UP_BUTTON_PREFIX,
    MOVE_ROW_DOWN_BUTTON_PREFIX,
)

SECTION_NAME: str = "Section name"
SECTION_CONTENT: str = "I am section content"

USER_NAME = "user1"
USER_PASSWORD = "bar"


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
        reverse("reports:report-publish", kwargs=report_pk_kwargs),
        follow=True,
    )

    assert response.status_code == 200

    assertContains(
        response,
        """HTML report successfully created!""",
    )


@pytest.mark.parametrize(
    "path_name, expected_header",
    [
        ("reports:report-detail", ">Edit report</h1>"),
        ("reports:edit-report-metadata", ">Report metadata</h1>"),
        ("reports:report-publisher", f"<p>{SECTION_CONTENT}</p>"),
        (
            "reports:report-confirm-refresh",
            ">Are you sure you want to reset the report?</h1>",
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


def test_edit_report_wrapper_page_non_staff_user(client, django_user_model):
    """
    Test that non-admin users are not given a UI to edit report wrapper text.
    """
    user = django_user_model.objects.create_user(
        username=USER_NAME, password=USER_PASSWORD
    )
    client.force_login(user)

    response = client.get(reverse("reports:edit-report-wrapper"))

    assertContains(response, "Admin access is required to edit the report viewer.")
    assertNotContains(
        response,
        """<input type="text" name="sent_by"
            value="[Government Digital Service](https://www.gov.uk/government/organisations/government-digital-service)"
            class="govuk-input" id="id_sent_by">""",
        html=True,
    )


def test_edit_report_wrapper_page_staff_user(client, django_user_model):
    """
    Test that admin users are given a UI to edit report wrapper text.
    """
    user = django_user_model.objects.create_user(
        username=USER_NAME, password=USER_PASSWORD, is_staff=True
    )
    client.force_login(user)

    response = client.get(reverse("reports:edit-report-wrapper"))

    assertNotContains(response, "Admin access is required to edit the report viewer.")
    assertContains(
        response,
        """<input type="text" name="sent_by"
            value="[Government Digital Service](https://www.gov.uk/government/organisations/government-digital-service)"
            class="govuk-input" id="id_sent_by">""",
        html=True,
    )


def test_report_details_page_shows_report_awaiting_approval(admin_client):
    """
    Test that the report details page shows a notification advising user to
    mark report as ready to review
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore
    case: Case = report.case  # type: ignore
    case.report_review_status = REPORT_READY_TO_REVIEW
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(
        response,
        "The report is waiting to be approved by the QA auditor.",
    )


@pytest.mark.parametrize(
    "path_name",
    [
        "cases:case-detail",
        "cases:edit-case-details",
        "cases:edit-test-results",
        "cases:edit-report-details",
        "cases:edit-qa-process",
    ],
)
def test_unpublished_report_data_updated_notification_shown(path_name, admin_client):
    """
    Test notification shown when report data (test result) more recent
    than latest report rebuild.
    """
    report: Report = create_report()
    report.report_rebuilt = timezone.now()
    report.save()
    audit: Audit = report.case.audit
    case_pk_kwargs: Dict[str, int] = {"pk": report.case.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs=case_pk_kwargs), follow=True
    )

    assert response.status_code == 200

    assertNotContains(
        response,
        "Data in the case has changed and information in the report is out of date.",
    )

    audit.unpublished_report_data_updated_time = timezone.now() + timedelta(hours=1)
    audit.save()

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs=case_pk_kwargs), follow=True
    )

    assert response.status_code == 200
    assertContains(
        response,
        "Data in the case has changed and information in the report is out of date.",
    )


@mock_s3
def test_published_report_data_updated_notification_shown(admin_client):
    """
    Test notification shown when report data (test result) more recent
    than latest report publish.
    """
    report: Report = create_report()
    audit: Audit = report.case.audit
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publish", kwargs=report_pk_kwargs), follow=True
    )

    assert response.status_code == 200

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs), follow=True
    )

    assert response.status_code == 200
    assertNotContains(
        response,
        "Data in the case has changed since the report was published.",
    )

    audit.published_report_data_updated_time = timezone.now() + timedelta(hours=1)
    audit.save()

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs), follow=True
    )

    assert response.status_code == 200
    assertContains(
        response,
        "Data in the case has changed since the report was published.",
    )


def test_report_metrics_displays_in_report_logs(admin_client):
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore
    case: Case = report.case  # type: ignore
    case.save()

    ReportVisitsMetrics.objects.create(
        case=case, fingerprint_hash=1234, fingerprint_codename="codename"
    )
    ReportVisitsMetrics.objects.create(
        case=case, fingerprint_hash=1234, fingerprint_codename="codename"
    )
    ReportVisitsMetrics.objects.create(
        case=case, fingerprint_hash=5678, fingerprint_codename="codename2"
    )
    url: str = f"""{reverse("reports:report-metrics-view", kwargs=report_pk_kwargs)}?showing=all"""
    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, "codename")
    assertContains(response, "codename2")
    assertContains(response, "Viewing 3 visits")
    assertContains(response, "Report visit logs")
    assertContains(response, "View unique visitors")

    url: str = f"""{reverse("reports:report-metrics-view", kwargs=report_pk_kwargs)}?showing=unique-visitors"""
    response: HttpResponse = admin_client.get(url)
    assert response.status_code == 200
    assertContains(response, "Viewing 2 visits")
    assertContains(response, "View all visits")

    url: str = f"""{reverse("reports:report-metrics-view", kwargs=report_pk_kwargs)}?userhash=codename2"""
    response: HttpResponse = admin_client.get(url)
    assert response.status_code == 200
    assertContains(response, "codename2")
    assertContains(response, "Viewing 1 visits")
    assertContains(response, "View all visits")


def test_issues_section_edit_page_contains_warning(admin_client):
    """
    Test that the edit section page for issues contains a warning to
    make changes in testing UI.
    """
    report: Report = create_report()
    audit_pk_kwargs: Dict[str, int] = {"pk": report.case.audit.id}
    test_details_url: str = reverse('audits:audit-detail', kwargs=audit_pk_kwargs)
    section: Section = create_section(report)
    section.template_type = TEMPLATE_TYPE_ISSUES_TABLE
    section.save()
    section_pk_kwargs: Dict[str, int] = {"pk": section.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse("reports:edit-report-section", kwargs=section_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<strong class="govuk-warning-text__text">
            <span class="govuk-warning-text__assistive">Warning</span>
            Edit test data in the
            <a href="{test_details_url}" class="govuk-link govuk-link--no-visited-state">
                testing application</a>
        </strong>""",
        html=True,
    )
