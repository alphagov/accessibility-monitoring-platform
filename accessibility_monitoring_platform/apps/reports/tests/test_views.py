"""
Tests for reports views
"""
import pytest
from typing import Dict
from datetime import timedelta

from moto import mock_s3

from pytest_django.asserts import assertContains, assertNotContains

from django.contrib.auth.models import User
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
    ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
    IS_WEBSITE_COMPLIANT_COMPLIANT,
)
from ...s3_read_write.models import S3Report

from ..models import (
    BaseTemplate,
    Report,
    ReportVisitsMetrics,
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


def create_section() -> BaseTemplate:
    """Create section in report"""
    return BaseTemplate.objects.create(
        name=SECTION_NAME, content=SECTION_CONTENT, position=1
    )


def test_create_report_redirects(admin_client):
    """Test that report create redirects to report publisher"""
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
        ("reports:edit-report-notes", ">Notes</h1>"),
        ("reports:report-publisher", f"<p>{SECTION_CONTENT}</p>"),
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
    create_section()

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, expected_header)


def test_report_publisher_page_shows_ready_to_review(admin_client):
    """
    Test that the report details page shows report is ready to review
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
    create_section()

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(
        response,
        "Mark the report as ready to review",
    )


def test_report_edit_notes_save_stays_on_page(admin_client):
    """
    Test that pressing the save button on report edit notes stays on the same page
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
    url: str = reverse("reports:edit-report-notes", kwargs=report_pk_kwargs)

    response: HttpResponse = admin_client.post(
        url,
        {
            "version": report.version,
            "save": "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == url


def test_report_edit_notes_redirects_to_publisher(admin_client):
    """Test that report edit notes redirects to report publisher on save"""
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
    url: str = reverse("reports:edit-report-notes", kwargs=report_pk_kwargs)

    response: HttpResponse = admin_client.post(
        url,
        {
            "version": report.version,
            "save_exit": "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("reports:report-publisher", kwargs=report_pk_kwargs)


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
    Test that the report details page tells user to review report
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
    case: Case = report.case
    user = User.objects.create()
    case.home_page_url = "https://www.website.com"
    case.organisation_name = "org name"
    case.auditor = user
    case.accessibility_statement_state = ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT
    case.is_website_compliant = IS_WEBSITE_COMPLIANT_COMPLIANT
    case.report_review_status = REPORT_READY_TO_REVIEW
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(
        response,
        "The report is waiting to be reviewed",
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
