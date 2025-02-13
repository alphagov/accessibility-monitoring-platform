"""
Tests for view - dashboard
"""

from datetime import date, datetime, timedelta

import pytest
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from accessibility_monitoring_platform.apps.common.models import ChangeToPlatform

from ...cases.models import Case, CaseCompliance, CaseStatus
from ...cases.utils import create_case_and_compliance
from ...common.models import Boolean
from ...notifications.models import Task


def test_dashboard_loads_correctly_when_user_logged_in(admin_client):
    """Tests if a logged in user can access the Dashboard"""
    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200
    assertContains(response, "Home |")


def test_dashboard_redirects_to_login_when_user_not_logged_in(client):
    """Tests if a unauthenticated user returns a 302 response"""
    url: str = reverse("dashboard:home")
    response: HttpResponse = client.get(url)

    assert response.status_code == 302
    assert response.url == f"/account/login/?next={url}"  # type: ignore


@pytest.mark.parametrize(
    "dashboard_view",
    ["View+your+cases", "View+all+cases"],
)
def test_dashboard_shows_qa_auditors(dashboard_view, admin_client):
    """Tests if dashboard views are showing the QA auditor"""
    response: HttpResponse = admin_client.get(
        f'{reverse("dashboard:home")}?view={dashboard_view}'
    )

    assert response.status_code == 200
    assertContains(response, "Active QA")


def test_dashboard_shows_oldest_unassigned_cases_first(admin_client):
    """Tests dashboard shows unassigned cases in order of oldest first"""
    case_1: Case = Case.objects.create(organisation_name="Organisation One")
    case_2: Case = Case.objects.create(organisation_name="Organisation Two")
    case_3: Case = Case.objects.create(organisation_name="Organisation Three")

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200

    content: str = str(response.content)
    case_1_position: int = content.index(case_1.organisation_name)
    case_2_position: int = content.index(case_2.organisation_name)
    case_3_position: int = content.index(case_3.organisation_name)

    assert case_1_position < case_2_position
    assert case_2_position < case_3_position


def test_dashboard_shows_link_to_closed_and_sent_cases(admin_client, admin_user):
    """Check dashboard contains link to find closed and sent to equalities body cases"""
    create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        case_completed=Case.CaseCompleted.COMPLETE_SEND,
        sent_to_enforcement_body_sent_date=datetime.now(),
    )

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200

    assertContains(
        response,
        f"""<a href="/cases/?auditor={admin_user.id}&status=case-closed-sent-to-equalities-body"
            class="govuk-link govuk-link--no-visited-state">
                View in search</a>""",
        html=True,
    )


def test_dashboard_shows_link_to_no_contact_email_sent(admin_client, admin_user):
    """Check dashboard contains link to find closed and sent to equalities body cases"""
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
    )

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200

    assertContains(
        response,
        f"""<a href="{reverse('cases:edit-qa-approval', kwargs={'pk': case.id})}" class="govuk-link">
            QA approval</a>""",
        html=True,
    )
    assertNotContains(
        response,
        f"""<a href="{reverse('cases:edit-request-contact-details', kwargs={'pk': case.id})}" class="govuk-link">
            No contact details request sent</a>""",
        html=True,
    )

    case.seven_day_no_contact_email_sent_date = date.today()
    case.save()

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200

    assertNotContains(
        response,
        f"""<a href="{reverse('cases:edit-qa-approval', kwargs={'pk': case.id})}" class="govuk-link">
            Report approved</a>""",
        html=True,
    )
    assertContains(
        response,
        f"""<a href="{reverse('cases:edit-request-contact-details', kwargs={'pk': case.id})}" class="govuk-link">
            No contact details request sent</a>""",
        html=True,
    )


def test_dashboard_shows_link_to_completed_cases(admin_client, admin_user):
    """Check dashboard contains link to find completed cases"""
    create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        case_completed=Case.CaseCompleted.COMPLETE_NO_SEND,
    )

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200

    assertContains(
        response,
        f"""<a href="/cases/?auditor={admin_user.id}&status=complete"
            class="govuk-link govuk-link--no-visited-state">
                View in search</a>""",
        html=True,
    )


def test_dashboard_shows_warning_of_recent_changes_to_platform(admin_client):
    """Check dashboard contains link to find completed cases"""
    ChangeToPlatform.objects.create(name="Recent change")

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200

    assertContains(
        response,
        f"""<div class="govuk-warning-text">
            <span class="govuk-warning-text__icon" aria-hidden="true">!</span>
            <strong class="govuk-warning-text__text">
                <span class="govuk-warning-text__assistive">Warning</span>
                An update has been made to the platform. View the update in
                <a href="{reverse("common:platform-history")}" class="govuk-link govuk-link--no-visited-state">
                    Settings &gt; Platform version history</a>
            </strong>
        </div>""",
        html=True,
    )


def test_dashboard_shows_correct_number_of_active_cases(admin_client, admin_user):
    """Check dashboard shows correct number of active cases"""
    # Creates unassigned case
    Case.objects.create()

    # Creates test in progress case
    Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
    )

    # Creates deactivated case
    Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        is_deactivated=True,
    )

    # Creates completed case
    create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        case_completed=Case.CaseCompleted.COMPLETE_SEND,
        sent_to_enforcement_body_sent_date=datetime.now(),
        enforcement_body_pursuing=Case.EnforcementBodyPursuing.YES_COMPLETED,
    )

    # Creates closed sent to equalities-body case
    create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        case_completed=Case.CaseCompleted.COMPLETE_SEND,
        sent_to_enforcement_body_sent_date=datetime.now(),
    )

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))
    assert Case.objects.all().count() == 5
    assert response.status_code == 200
    expected_number_of_active_cases: str = """
    <p class="govuk-body amp-margin-bottom-10"><b>Total active cases</b></p>
    <p class="govuk-body amp-margin-bottom-10">2</p>
    """
    assertContains(
        response,
        expected_number_of_active_cases,
        html=True,
    )


def test_dashboard_shows_correct_number_of_your_active_cases(admin_client, admin_user):
    """Check dashboard shows correct number of your active cases"""

    # Creates unassigned case
    Case.objects.create()
    Case.objects.create()

    # Case assigned to you
    Case.objects.create(auditor=admin_user)

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))
    assert Case.objects.all().count() == 3
    assert response.status_code == 200
    expected_number_of_your_active_cases: str = """
    <p class="govuk-body amp-margin-bottom-10"><b>Your active cases</b></p>
    <p class="govuk-body amp-margin-bottom-10">1</p>
    """
    assertContains(
        response,
        expected_number_of_your_active_cases,
        html=True,
    )

    expected_number_of_unnassigned_cases: str = """
    <p class="govuk-body amp-margin-bottom-10"><b>Unassigned cases</b></p>
    <p class="govuk-body amp-margin-bottom-10">2</p>
    """
    assertContains(
        response,
        expected_number_of_unnassigned_cases,
        html=True,
    )


def test_dashboard_shows_link_to_reminder_reviewing(admin_client, admin_user):
    """
    Tests dashboard shows link to reminder for cases of status
    reviewing changes
    """
    case: Case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
    )
    case.compliance.statement_compliance_state_initial = (
        CaseCompliance.StatementCompliance.COMPLIANT
    )
    case.compliance.website_compliance_state_initial = (
        CaseCompliance.WebsiteCompliance.COMPLIANT
    )
    case.compliance.save()
    case.save()
    task: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today() + timedelta(days=10),
        user=admin_user,
        case=case,
    )

    assert case.status.status == CaseStatus.Status.REVIEWING_CHANGES

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200

    assertContains(
        response,
        reverse("notifications:edit-reminder-task", kwargs={"pk": task.id}),
    )


def test_dashboard_shows_link_to_reminder_final(admin_client, admin_user):
    """
    Tests dashboard shows link to reminder for cases of status
    final decision due
    """
    case: Case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        no_psb_contact=Boolean.YES,
    )
    case.compliance.statement_compliance_state_initial = (
        CaseCompliance.StatementCompliance.COMPLIANT
    )
    case.compliance.website_compliance_state_initial = (
        CaseCompliance.WebsiteCompliance.COMPLIANT
    )
    case.compliance.save()
    case.save()
    task: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today() + timedelta(days=10),
        user=admin_user,
        case=case,
    )

    assert case.status.status == CaseStatus.Status.FINAL_DECISION_DUE

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200

    assertContains(
        response,
        reverse("notifications:edit-reminder-task", kwargs={"pk": task.id}),
    )
