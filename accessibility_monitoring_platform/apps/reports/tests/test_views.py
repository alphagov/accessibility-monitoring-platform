"""
Tests for reports views
"""
import pytest
from typing import Dict

from moto import mock_s3

from pytest_django.asserts import assertContains, assertNotContains

from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse

from ...audits.models import (
    Audit,
    CheckResult,
    Page,
    WcagDefinition,
    PAGE_TYPE_STATEMENT,
    TEST_TYPE_AXE,
    CHECK_RESULT_ERROR,
)
from ...audits.utils import report_data_updated
from ...cases.models import (
    Case,
    CaseEvent,
    REPORT_APPROVED_STATUS_APPROVED,
    CASE_EVENT_CREATE_REPORT,
    ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
    WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
)
from ...common.models import BOOLEAN_TRUE
from ...s3_read_write.models import S3Report

from ..models import (
    Report,
    ReportVisitsMetrics,
)

WCAG_TYPE_AXE_NAME: str = "WCAG Axe name"
HOME_PAGE_URL: str = "https://example.com"
CHECK_RESULTS_NOTES: str = "I am an error note"
EXTRA_STATEMENT_WORDING: str = "Extra statement wording"

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
    assert number_of_s3_reports == 0

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publish", kwargs=report_pk_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    assert S3Report.objects.filter(case=report.case).count() == 1
    assert (
        S3Report.objects.filter(case=report.case).filter(latest_published=True).count()
        == 1
    )


@mock_s3
def test_old_published_report_includes_errors(admin_client):
    """
    Test that published report contains the test results
    """
    report: Report = create_report()
    report.report_version = "v1_1_0__20230421"
    report.save()
    audit: Audit = report.case.audit
    audit.accessibility_statement_report_text_wording = EXTRA_STATEMENT_WORDING
    audit.save()
    page: Page = Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_STATEMENT, url=HOME_PAGE_URL
    )
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=TEST_TYPE_AXE, name=WCAG_TYPE_AXE_NAME
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CHECK_RESULT_ERROR,
        notes=CHECK_RESULTS_NOTES,
    )

    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publish", kwargs=report_pk_kwargs),
    )

    assert response.status_code == 302

    s3_report: S3Report = S3Report.objects.get(case=report.case)

    assert HOME_PAGE_URL in s3_report.html
    assert WCAG_TYPE_AXE_NAME in s3_report.html
    assert CHECK_RESULTS_NOTES in s3_report.html
    assert EXTRA_STATEMENT_WORDING in s3_report.html


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
        (
            "reports:report-publisher",
            "<li>which parts of your website we looked at</li>",
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

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, expected_header)


def test_button_to_published_report_shown(admin_client):
    """
    Test button link to published report shown if published report exists
    """
    case: Case = Case.objects.create()
    Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, "View final HTML report")
    assertContains(response, "Republish HTML report")
    assertNotContains(response, "Publish HTML report")


def test_button_to_published_report_not_shown(admin_client):
    """
    Test button link to published report not shown if report not published
    """
    case: Case = Case.objects.create()
    Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertNotContains(response, "View final HTML report")
    assertNotContains(response, "Republish HTML report")
    assertContains(response, "Publish HTML report")


def test_report_next_step_for_not_started(admin_client):
    """
    Test report next step for report review not started
    """
    case: Case = Case.objects.create()
    Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, "Mark the report as ready to review")
    assertContains(response, "Go to QA process")


def test_report_next_step_for_case_unassigned_qa(admin_client):
    """
    Test report next step for unassigned qa case
    """
    user: User = User.objects.create()
    case: Case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
    )
    Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, "The report is waiting to be reviewed")
    assertContains(response, "Go to QA process")


def test_report_next_step_for_case_qa_in_progress(admin_client):
    """
    Test report next step for case in qa in progress
    """
    user: User = User.objects.create()
    case: Case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
    )
    Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, "The report is waiting to be reviewed")
    assertContains(response, "Go to QA process")


def test_report_next_step_for_case_report_approved(admin_client):
    """
    Test report next step for case report approved status is 'yes'
    """
    case: Case = Case.objects.create(
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
    )
    Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(
        response, "The report has been approved and is ready to be published"
    )
    assertContains(response, "Publish HTML report")


def test_report_next_step_for_published_report_out_of_date(admin_client):
    """
    Test report next step for published report is out of date
    """
    case: Case = Case.objects.create(
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
    )
    audit: Audit = Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)
    report_data_updated(audit=audit)
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(
        response,
        "The platform has identified changes to the test since publishing the report.",
    )
    assertContains(response, "Republish the report")


def test_report_next_step_for_published_report(admin_client):
    """
    Test report next step for published report
    """
    case: Case = Case.objects.create(
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
    )
    Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0, latest_published=True)
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, "The report has been published.")
    assertContains(response, "Return to Case &gt; Report details")


def test_report_next_step_default(admin_client):
    """
    Test report next stepdefault
    """
    case: Case = Case.objects.create(
        report_review_status=BOOLEAN_TRUE,
        report_approved_status="in-progress",
    )
    Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

    response: HttpResponse = admin_client.get(
        reverse("reports:report-publisher", kwargs=report_pk_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, "The report is not yet ready")
    assertContains(response, "Go to Testing details")


def test_report_publisher_page_shows_ready_to_review(admin_client):
    """
    Test that the report details page shows report is ready to review
    """
    report: Report = create_report()
    report_pk_kwargs: Dict[str, int] = {"pk": report.id}

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
    case.website_compliance_state_initial = WEBSITE_INITIAL_COMPLIANCE_COMPLIANT
    case.report_review_status = BOOLEAN_TRUE
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
