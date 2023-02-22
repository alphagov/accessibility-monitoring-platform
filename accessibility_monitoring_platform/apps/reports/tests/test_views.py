"""
Tests for reports views
"""
import pytest
from typing import Dict
from datetime import timedelta

from moto import mock_s3

from pytest_django.asserts import assertContains, assertNotContains

from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from ...audits.models import (
    Audit,
)
from ...cases.models import (
    Case,
    CaseEvent,
    REPORT_APPROVED_STATUS_APPROVED,
    REPORT_READY_TO_REVIEW,
    CASE_EVENT_CREATE_REPORT,
)
from ...s3_read_write.models import S3Report

from ..models import (
    Report,
    TableRow,
    Section,
    ReportVisitsMetrics,
    TEMPLATE_TYPE_URLS,
    TEMPLATE_TYPE_ISSUES_TABLE,
)
from ..utils import (
    DELETE_ROW_BUTTON_PREFIX,
    UNDELETE_ROW_BUTTON_PREFIX,
    MOVE_ROW_UP_BUTTON_PREFIX,
    MOVE_ROW_DOWN_BUTTON_PREFIX,
)

SECTION_NAME: str = "Section name"
SECTION_CONTENT: str = "I am section content"

USER_NAME: str = "user1"
USER_PASSWORD: str = "bar"

FIRST_CODENAME: str = "FirstCodename"
SECOND_CODENAME: str = "SecondCodename"


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
    path_kwargs: Dict[str, int] = {"case_id": case.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-create", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse("reports:report-publisher", kwargs={"pk": 1})


def test_create_report_does_not_create_duplicate(admin_client):
    """Test that report create does not create a duplicate report"""
    report: Report = create_report()
    path_kwargs: Dict[str, int] = {"case_id": report.case.id}

    assert Report.objects.filter(case=report.case).count() == 1

    response: HttpResponse = admin_client.get(
        reverse("reports:report-create", kwargs=path_kwargs),
    )

    assert response.status_code == 302
    assert Report.objects.filter(case=report.case).count() == 1


def test_create_report_creates_case_event(admin_client):
    """Test that report create al creates a case event"""
    case: Case = Case.objects.create()
    path_kwargs: Dict[str, int] = {"case_id": case.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-create", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(case=case)
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CASE_EVENT_CREATE_REPORT
    assert case_event.message == "Created report"


@pytest.mark.parametrize(
    "return_to, expected_redirect",
    [
        ("edit-report", "reports:edit-report"),
        ("report-publisher", "reports:report-publisher"),
        ("", "reports:report-publisher"),
    ],
)
def test_rebuild_report_redirects(return_to, expected_redirect, admin_client):
    """Test that report rebuild redirects correctly"""
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        f"{reverse('reports:report-rebuild', kwargs=report_pk_kwargs)}?return_to={return_to}",
    )

    assert response.status_code == 302

    assert response.url == reverse(expected_redirect, kwargs=report_pk_kwargs)


@mock_s3
def test_publish_report_redirects(admin_client):
    """
    Test that report publish redirects to report details
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
    number_of_s3_reports: int = S3Report.objects.filter(case=report.case).count()

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publish", kwargs=report_pk_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    assert S3Report.objects.filter(case=report.case).count() == number_of_s3_reports + 1
    assert (
        S3Report.objects.filter(case=report.case).filter(latest_published=True).count()
        == 1
    )


@mock_s3
def test_report_published_message_shown(admin_client):
    """Test publishing the report causes a message to be shown on the next page"""
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

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
        ("reports:edit-report", ">Edit report</h1>"),
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
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
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
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
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
    section_pk_kwargs: Dict[str, int] = {"pk": section.id}

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
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
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
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
    url: str = reverse("reports:edit-report-metadata", kwargs=report_pk_kwargs)

    response: HttpResponse = admin_client.post(
        url,
        {
            "version": report.version,
            "save_exit": "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("reports:edit-report", kwargs=report_pk_kwargs)


@pytest.mark.django_db
def test_report_edit_section_save_button_stays_on_page(admin_client):
    """Test pressing save button on report edit section stays on page"""
    report: Report = create_report()
    section: Section = create_section(report)
    section_pk_kwargs: Dict[str, int] = {"pk": section.id}
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
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
    section: Section = create_section(report)
    section_pk_kwargs: Dict[str, int] = {"pk": section.id}
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
    assert response.url == reverse("reports:edit-report", kwargs=report_pk_kwargs)


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
    section_pk_kwargs: Dict[str, int] = {"pk": section.id}
    table_row: TableRow = TableRow.objects.create(section=section, row_number=1)
    table_row_id: int = table_row.id
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


def test_unapproved_report_confirm_publish_asks_for_approval(admin_client):
    """
    Test that the confirm publish page asks for report to be QA approved
    when it has not been.
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

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
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
    case: Case = report.case
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
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
    case: Case = report.case
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
    case_pk_kwargs: Dict[str, int] = {"pk": report.case.id}

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
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

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
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
    case: Case = report.case
    case.save()

    ReportVisitsMetrics.objects.create(
        case=case, fingerprint_hash=1234, fingerprint_codename=FIRST_CODENAME
    )
    ReportVisitsMetrics.objects.create(
        case=case, fingerprint_hash=1234, fingerprint_codename=FIRST_CODENAME
    )
    ReportVisitsMetrics.objects.create(
        case=case, fingerprint_hash=5678, fingerprint_codename=SECOND_CODENAME
    )
    url: str = f"""{reverse("reports:report-metrics-view", kwargs=report_pk_kwargs)}?showing=all"""
    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, FIRST_CODENAME)
    assertContains(response, SECOND_CODENAME)
    assertContains(response, "Viewing 3 visits")
    assertContains(response, "Report visit logs")
    assertContains(response, "View unique visitors")

    url: str = f"""{reverse("reports:report-metrics-view", kwargs=report_pk_kwargs)}?showing=unique-visitors"""
    response: HttpResponse = admin_client.get(url)
    assert response.status_code == 200
    assertContains(response, "Viewing 2 visits")
    assertContains(response, "View all visits")

    # Check unique visitors are sorted by most recent visit first
    html: str = response.content.decode()
    assert html.index(FIRST_CODENAME) > html.index(SECOND_CODENAME)

    url: str = f'{reverse("reports:report-metrics-view", kwargs=report_pk_kwargs)}?userhash={SECOND_CODENAME}'
    response: HttpResponse = admin_client.get(url)
    assert response.status_code == 200
    assertContains(response, SECOND_CODENAME)
    assertContains(response, "Viewing 1 visits")
    assertContains(response, "View all visits")


def test_issues_section_edit_page_contains_warning(admin_client):
    """
    Test that the edit section page for issues contains a warning to
    make changes in testing UI.
    """
    report: Report = create_report()
    audit_pk_kwargs: Dict[str, int] = {"pk": report.case.audit.id}  # type: ignore
    test_details_url: str = reverse("audits:audit-detail", kwargs=audit_pk_kwargs)
    section: Section = create_section(report)
    section.template_type = TEMPLATE_TYPE_ISSUES_TABLE
    section.save()
    section_pk_kwargs: Dict[str, int] = {"pk": section.id}

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


@pytest.mark.parametrize(
    "section_type,table_header_1,table_header_2",
    [
        (TEMPLATE_TYPE_URLS, "Page Name", "URL"),
        (
            TEMPLATE_TYPE_ISSUES_TABLE,
            "Issue and description",
            "Where the issue was found",
        ),
    ],
)
def test_section_edit_page_tables_use_hidden_labels(
    section_type, table_header_1, table_header_2, admin_client
):
    """
    Test that the edit section page for report pages with tables
    contain visually hidden labels in their tables.
    """
    report: Report = create_report()
    section: Section = create_section(report)
    section.template_type = section_type
    section.save()
    section_pk_kwargs: Dict[str, int] = {"pk": section.id}
    TableRow.objects.create(section=section, row_number=1)

    response: HttpResponse = admin_client.get(
        reverse("reports:edit-report-section", kwargs=section_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(
        response,
        f"""<div class="govuk-form-group">
            <label
                id="id_form-0-cell_content_1-label"
                class="govuk-visually-hidden"
                for="id_form-0-cell_content_1">
                {table_header_1} 1
            </label>
            <textarea
                name="form-0-cell_content_1"
                cols="40"
                rows="4"
                class="govuk-textarea"
                id="id_form-0-cell_content_1">
            </textarea>
        </div>""",
        html=True,
    )

    assertContains(
        response,
        f"""<div class="govuk-form-group">
            <label
                id="id_form-0-cell_content_2-label"
                class="govuk-visually-hidden"
                for="id_form-0-cell_content_2">
                {table_header_2} 1
            </label>
            <textarea
                name="form-0-cell_content_2"
                cols="40"
                rows="4"
                class="govuk-textarea"
                id="id_form-0-cell_content_2">
            </textarea>
        </div>""",
        html=True,
    )
