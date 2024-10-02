"""
Tests for reports views
"""

from datetime import datetime, timezone
from typing import Dict
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from moto import mock_aws
from pytest_django.asserts import assertContains, assertNotContains

from ...audits.models import (
    Audit,
    CheckResult,
    Page,
    StatementCheckResult,
    WcagDefinition,
)
from ...audits.utils import report_data_updated
from ...cases.models import Case, CaseCompliance, CaseEvent
from ...cases.utils import create_case_and_compliance
from ...common.models import Boolean
from ...s3_read_write.models import S3Report
from ..models import REPORT_VERSION_DEFAULT, Report, ReportVisitsMetrics

WCAG_TYPE_AXE_NAME: str = "WCAG Axe name"
HOME_PAGE_URL: str = "https://example.com"
CHECK_RESULTS_NOTES: str = "I am an error note"
EXTRA_STATEMENT_WORDING: str = "Extra statement wording"
PAGE_LOCATION: str = "Click on second link"

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


def test_create_report_uses_older_template(admin_client):
    """
    Test that report create uses last pre-statement check report template if no
    statement checks exist
    """
    case: Case = Case.objects.create()
    path_kwargs: Dict[str, int] = {"case_id": case.id}
    Audit.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("reports:report-create", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    report: Report = Report.objects.get(case=case)

    assert report.report_version == "v1_1_0__20230421"


def test_create_report_uses_latest_template(admin_client):
    """
    Test that report create uses latest report template if statement checks
    exist
    """
    case: Case = Case.objects.create()
    path_kwargs: Dict[str, int] = {"case_id": case.id}
    audit: Audit = Audit.objects.create(case=case)
    StatementCheckResult.objects.create(audit=audit)

    response: HttpResponse = admin_client.get(
        reverse("reports:report-create", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    report: Report = Report.objects.get(case=case)

    assert report.report_version == REPORT_VERSION_DEFAULT


def test_create_report_redirects(admin_client):
    """Test that report create redirects to report publisher"""
    case: Case = Case.objects.create()
    path_kwargs: Dict[str, int] = {"case_id": case.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-create", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse("cases:edit-report-ready-for-qa", kwargs={"pk": 1})


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
    assert case_event.event_type == CaseEvent.EventType.CREATE_REPORT
    assert case_event.message == "Created report"


@mock_aws
def test_old_published_report_includes_errors(admin_client):
    """
    Test that published report contains the test results
    """
    report: Report = create_report()
    report.report_version = "v1_1_0__20230421"
    report.save()
    audit: Audit = report.case.audit
    audit.archive_accessibility_statement_report_text_wording = EXTRA_STATEMENT_WORDING
    audit.save()
    page: Page = Page.objects.create(
        audit=audit, page_type=Page.Type.STATEMENT, url=HOME_PAGE_URL
    )
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name=WCAG_TYPE_AXE_NAME
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
        notes=CHECK_RESULTS_NOTES,
    )

    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-preview", kwargs=report_pk_kwargs),
    )

    assert response.status_code == 200

    assertContains(response, HOME_PAGE_URL)
    assertContains(response, WCAG_TYPE_AXE_NAME)
    assertContains(response, CHECK_RESULTS_NOTES)
    assertContains(response, EXTRA_STATEMENT_WORDING)


def test_report_includes_page_location(admin_client):
    """
    Test that report contains the page location
    """
    report: Report = create_report()
    audit: Audit = report.case.audit
    Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url=HOME_PAGE_URL, location=PAGE_LOCATION
    )

    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-preview", kwargs=report_pk_kwargs),
    )

    assert response.status_code == 200
    assertContains(response, PAGE_LOCATION)


@pytest.mark.parametrize(
    "path_name, expected_header",
    [
        (
            "reports:report-preview",
            "<li>which parts of your website we looked at</li>",
        ),
    ],
)
def test_report_specific_page_loads(path_name, expected_header, admin_client):
    """Test that the report-specific page loads"""
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, expected_header)


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
    case: Case = report.case
    case_pk_kwargs: Dict[str, int] = {"pk": case.id}
    user = User.objects.create()
    case.home_page_url = "https://www.website.com"
    case.organisation_name = "org name"
    case.auditor = user
    case.report_review_status = Boolean.YES
    case.compliance.statement_compliance_state_initial = (
        CaseCompliance.StatementCompliance.COMPLIANT
    )
    case.compliance.website_compliance_state_initial = (
        CaseCompliance.WebsiteCompliance.COMPLIANT
    )
    case.compliance.save()
    case.save()

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-publish-report", kwargs=case_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(
        response,
        "To publish this report, you need to:",
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
    url: str = (
        f"""{reverse("reports:report-metrics-view", kwargs=report_pk_kwargs)}?showing=all"""
    )
    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200

    assertContains(response, FIRST_CODENAME)
    assertContains(response, SECOND_CODENAME)
    assertContains(response, "Viewing 3 visits")
    assertContains(response, "Report visit logs")
    assertContains(response, "View unique visitors")

    url: str = (
        f"""{reverse("reports:report-metrics-view", kwargs=report_pk_kwargs)}?showing=unique-visitors"""
    )
    response: HttpResponse = admin_client.get(url)
    assert response.status_code == 200
    assertContains(response, "Viewing 2 visits")
    assertContains(response, "View all visits")

    # Check unique visitors are sorted by most recent visit first
    html: str = response.content.decode()
    assert html.index(FIRST_CODENAME) > html.index(SECOND_CODENAME)

    url: str = (
        f'{reverse("reports:report-metrics-view", kwargs=report_pk_kwargs)}?userhash={SECOND_CODENAME}'
    )
    response: HttpResponse = admin_client.get(url)
    assert response.status_code == 200
    assertContains(response, SECOND_CODENAME)
    assertContains(response, "Viewing 1 visits")
    assertContains(response, "View all visits")


def test_report_metrics_unique_vists_shows_only_current_report(admin_client):
    """
    Visits to other reports can have the same fingerprint hash, make sure
    that they are not included.
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}
    case: Case = report.case
    case.save()
    other_case: Case = Case.objects.create()

    ReportVisitsMetrics.objects.create(
        case=case, fingerprint_hash=1234, fingerprint_codename=FIRST_CODENAME
    )
    ReportVisitsMetrics.objects.create(
        case=case, fingerprint_hash=1234, fingerprint_codename=FIRST_CODENAME
    )
    with patch(
        "django.utils.timezone.now",
        Mock(return_value=datetime(2020, 1, 5, tzinfo=timezone.utc)),
    ):
        ReportVisitsMetrics.objects.create(
            case=other_case, fingerprint_hash=5678, fingerprint_codename=SECOND_CODENAME
        )
    ReportVisitsMetrics.objects.create(
        case=case, fingerprint_hash=5678, fingerprint_codename=SECOND_CODENAME
    )

    url: str = (
        f"""{reverse("reports:report-metrics-view", kwargs=report_pk_kwargs)}?showing=unique-visitors"""
    )
    response: HttpResponse = admin_client.get(url)
    assert response.status_code == 200
    assertNotContains(response, "2020-01-05")
