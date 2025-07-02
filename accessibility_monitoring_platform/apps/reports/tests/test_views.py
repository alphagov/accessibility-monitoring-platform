"""
Tests for reports views
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from ...audits.models import (
    Audit,
    Page,
    StatementCheck,
    StatementCheckResult,
    StatementPage,
)
from ...common.models import Boolean
from ...simplified.models import CaseCompliance, CaseEvent, SimplifiedCase
from ..models import REPORT_VERSION_DEFAULT, Report, ReportVisitsMetrics

USER_NAME: str = "user1"
USER_PASSWORD: str = "bar"
HOME_PAGE_URL: str = "https://example.com"
PAGE_LOCATION: str = "Click on second link"
FIRST_CODENAME: str = "FirstCodename"
SECOND_CODENAME: str = "SecondCodename"
STATEMENT_CUSTOM_CHECK_COMMENT: str = "Statement custom check result comment"


def create_report() -> Report:
    """Create a report"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    Audit.objects.create(simplified_case=simplified_case)
    report: Report = Report.objects.create(base_case=simplified_case)
    return report


def test_create_report_uses_latest_template(admin_client):
    """Test that report create uses latest report template"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    path_kwargs: dict[str, int] = {"case_id": simplified_case.id}
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    StatementCheckResult.objects.create(audit=audit)

    response: HttpResponse = admin_client.get(
        reverse("reports:report-create", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    report: Report = Report.objects.get(base_case=simplified_case)

    assert report.report_version == REPORT_VERSION_DEFAULT


def test_create_report_redirects(admin_client):
    """Test that report create redirects to report publisher"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    path_kwargs: dict[str, int] = {"case_id": simplified_case.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-create", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse(
        "simplified:edit-report-ready-for-qa", kwargs={"pk": 1}
    )


def test_create_report_does_not_create_duplicate(admin_client):
    """Test that report create does not create a duplicate report"""
    report: Report = create_report()
    path_kwargs: dict[str, int] = {"case_id": report.base_case.id}

    assert Report.objects.filter(base_case=report.base_case).count() == 1

    response: HttpResponse = admin_client.get(
        reverse("reports:report-create", kwargs=path_kwargs),
    )

    assert response.status_code == 302
    assert Report.objects.filter(base_case=report.base_case).count() == 1


def test_create_report_creates_case_event(admin_client):
    """Test that report create al creates a case event"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    path_kwargs: dict[str, int] = {"case_id": simplified_case.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-create", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    case_events: QuerySet[CaseEvent] = CaseEvent.objects.filter(
        simplified_case=simplified_case
    )
    assert case_events.count() == 1

    case_event: CaseEvent = case_events[0]
    assert case_event.event_type == CaseEvent.EventType.CREATE_REPORT
    assert case_event.message == "Created report"


def test_report_includes_page_location(admin_client):
    """
    Test that report contains the page location
    """
    report: Report = create_report()
    audit: Audit = report.base_case.simplifiedcase.audit
    Page.objects.create(
        audit=audit, page_type=Page.Type.HOME, url=HOME_PAGE_URL, location=PAGE_LOCATION
    )

    report_pk_kwargs: dict[str, int] = {"pk": report.id}

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
    report_pk_kwargs: dict[str, int] = {"pk": report.id}

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
    simplified_case: SimplifiedCase = report.base_case
    case_pk_kwargs: dict[str, int] = {"pk": simplified_case.id}
    user = User.objects.create()
    simplified_case.home_page_url = "https://www.website.com"
    simplified_case.organisation_name = "org name"
    simplified_case.auditor = user
    simplified_case.report_review_status = Boolean.YES
    simplified_case.compliance.statement_compliance_state_initial = (
        CaseCompliance.StatementCompliance.COMPLIANT
    )
    simplified_case.compliance.website_compliance_state_initial = (
        CaseCompliance.WebsiteCompliance.COMPLIANT
    )
    simplified_case.compliance.save()
    simplified_case.save()

    response: HttpResponse = admin_client.get(
        reverse("simplified:edit-publish-report", kwargs=case_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(
        response,
        "To publish this report, you need to:",
    )


def test_report_metrics_displays_in_report_logs(admin_client):
    report: Report = create_report()
    report_pk_kwargs: dict[str, int] = {"pk": report.id}
    simplified_case: SimplifiedCase = report.base_case
    simplified_case.save()

    ReportVisitsMetrics.objects.create(
        base_case=simplified_case,
        fingerprint_hash=1234,
        fingerprint_codename=FIRST_CODENAME,
    )
    ReportVisitsMetrics.objects.create(
        base_case=simplified_case,
        fingerprint_hash=1234,
        fingerprint_codename=FIRST_CODENAME,
    )
    ReportVisitsMetrics.objects.create(
        base_case=simplified_case,
        fingerprint_hash=5678,
        fingerprint_codename=SECOND_CODENAME,
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
    report_pk_kwargs: dict[str, int] = {"pk": report.id}
    simplified_case: SimplifiedCase = report.base_case
    other_simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    ReportVisitsMetrics.objects.create(
        base_case=simplified_case,
        fingerprint_hash=1234,
        fingerprint_codename=FIRST_CODENAME,
    )
    ReportVisitsMetrics.objects.create(
        base_case=simplified_case,
        fingerprint_hash=1234,
        fingerprint_codename=FIRST_CODENAME,
    )
    with patch(
        "django.utils.timezone.now",
        Mock(return_value=datetime(2020, 1, 5, tzinfo=timezone.utc)),
    ):
        ReportVisitsMetrics.objects.create(
            base_case=other_simplified_case,
            fingerprint_hash=5678,
            fingerprint_codename=SECOND_CODENAME,
        )
    ReportVisitsMetrics.objects.create(
        base_case=simplified_case,
        fingerprint_hash=5678,
        fingerprint_codename=SECOND_CODENAME,
    )

    url: str = (
        f"""{reverse("reports:report-metrics-view", kwargs=report_pk_kwargs)}?showing=unique-visitors"""
    )
    response: HttpResponse = admin_client.get(url)
    assert response.status_code == 200
    assertNotContains(response, "2020-01-05")


def test_report_includes_statement_custom_issue(admin_client):
    """
    Test that report contains the page location
    """
    report: Report = create_report()
    audit: Audit = report.base_case.simplifiedcase.audit
    StatementPage.objects.create(audit=audit, url="https://example.com")

    report_pk_kwargs: dict[str, int] = {"pk": report.id}

    for statement_check_result in StatementCheckResult.objects.filter(
        type=StatementCheck.Type.CUSTOM
    ):
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    response: HttpResponse = admin_client.post(
        reverse("audits:edit-custom-issue-create", kwargs={"audit_id": audit.id}),
        {"report_comment": STATEMENT_CUSTOM_CHECK_COMMENT, "save": "Save and return"},
    )

    assert response.status_code == 302

    response: HttpResponse = admin_client.get(
        reverse("reports:report-preview", kwargs=report_pk_kwargs),
    )

    assert response.status_code == 200
    assertContains(response, STATEMENT_CUSTOM_CHECK_COMMENT)
