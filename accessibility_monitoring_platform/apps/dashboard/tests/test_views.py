"""
Tests for view - dashboard
"""
import pytest

from datetime import datetime

from pytest_django.asserts import assertContains

from django.http import HttpResponse
from django.urls import reverse

from ...cases.models import (
    Case,
    ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
    IS_WEBSITE_COMPLIANT_COMPLIANT,
    CASE_COMPLETED_NO_SEND,
    REPORT_READY_TO_REVIEW,
    REPORT_APPROVED_STATUS_APPROVED,
    CASE_COMPLETED_SEND,
)


def test_dashboard_loads_correctly_when_user_logged_in(admin_client):
    """Tests if a logged in user can access the Dashboard"""
    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200
    assertContains(response, "Dashboard")


def test_dashboard_redirects_to_login_when_user_not_logged_in(client):
    """Tests if a unauthenticated user returns a 302 response"""
    url: str = reverse("dashboard:home")
    response: HttpResponse = client.get(url)

    assert response.status_code == 302
    assert response.url == f"/account/login/?next={url}"  # type: ignore


@pytest.mark.parametrize(
    "dashboard_view, expected_qa_column",
    [
        ("View+your+cases", "On call"),
        ("View+all+cases", "Unassigned QA cases"),
    ],
)
def test_dashboard_shows_qa_auditors(dashboard_view, expected_qa_column, admin_client):
    """Tests if dashboard views are showing the expected QA auditors column"""
    response: HttpResponse = admin_client.get(
        f'{reverse("dashboard:home")}?view={dashboard_view}'
    )

    assert response.status_code == 200
    assertContains(response, expected_qa_column)


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
    Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        report_review_status=REPORT_READY_TO_REVIEW,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        case_completed=CASE_COMPLETED_SEND,
        sent_to_enforcement_body_sent_date=datetime.now(),
    )

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200

    assertContains(
        response,
        f"""<p class="govuk-body">
            <a href="/cases/?auditor={admin_user.id}&status=case-closed-sent-to-equalities-body" class="govuk-link">
                View all your cases with status "Case closed and sent to equalities body"</a>
        </p>""",
        html=True,
    )


def test_dashboard_shows_link_to_completed_cases(admin_client, admin_user):
    """Check dashboard contains link to find completed cases"""
    Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        case_completed=CASE_COMPLETED_NO_SEND,
    )

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200

    assertContains(
        response,
        f"""<p class="govuk-body">
            <a href="/cases/?auditor={admin_user.id}&status=complete" class="govuk-link">
                View all your cases with status "Complete"</a>
        </p>""",
        html=True,
    )
