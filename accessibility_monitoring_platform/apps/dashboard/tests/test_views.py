"""
Tests for view - dashboard
"""
import pytest

from datetime import datetime
from typing import Any, Dict

from pytest_django.asserts import assertContains

from django.http import HttpResponse
from django.urls import reverse

from accessibility_monitoring_platform.apps.common.models import ChangeToPlatform

from ...cases.models import (
    Case,
    CaseCompliance,
    COMPLIANCE_FIELDS,
    ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
    WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
    CASE_COMPLETED_NO_SEND,
    REPORT_APPROVED_STATUS_APPROVED,
    CASE_COMPLETED_SEND,
    ENFORCEMENT_BODY_PURSUING_YES_COMPLETED,
)
from ...common.models import BOOLEAN_TRUE


def create_case(**kwargs):
    compliance_kwargs: Dict[str, Any] = {
        key: value for key, value in kwargs.items() if key in COMPLIANCE_FIELDS
    }
    non_compliance_args: Dict[str, Any] = {
        key: value for key, value in kwargs.items() if key not in COMPLIANCE_FIELDS
    }
    case: Case = Case.objects.create(**non_compliance_args)
    CaseCompliance.objects.create(case=case, **compliance_kwargs)
    case.save()
    return case


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
    """Tests if dashboard views are showing the expected QA auditors column"""
    response: HttpResponse = admin_client.get(
        f'{reverse("dashboard:home")}?view={dashboard_view}'
    )

    assert response.status_code == 200
    assertContains(response, "On call")


def test_dashboard_shows_oldest_unassigned_cases_first(admin_client):
    """Tests dashboard shows unassigned cases in order of oldest first"""
    case_1: Case = create_case(organisation_name="Organisation One")
    case_2: Case = create_case(organisation_name="Organisation Two")
    case_3: Case = create_case(organisation_name="Organisation Three")

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
    create_case(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
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
    create_case(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
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
    create_case()

    # Creates test in progress case
    create_case(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
    )

    # Creates deactivated case
    create_case(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        is_deactivated=True,
    )

    # Creates completed case
    create_case(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        case_completed=CASE_COMPLETED_SEND,
        sent_to_enforcement_body_sent_date=datetime.now(),
        enforcement_body_pursuing=ENFORCEMENT_BODY_PURSUING_YES_COMPLETED,
    )

    # Creates closed sent to equalities-body case
    create_case(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=admin_user,
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        case_completed=CASE_COMPLETED_SEND,
        sent_to_enforcement_body_sent_date=datetime.now(),
    )

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))
    assert Case.objects.all().count() == 5
    assert response.status_code == 200
    expected_number_of_active_cases: str = """
    <div class="govuk-body-m"> Total active cases </div>
    <div class="govuk-heading-xl amp-margin-bottom-0"> 2 </div>
    """
    assertContains(
        response,
        expected_number_of_active_cases,
        html=True,
    )


def test_dashboard_shows_correct_number_of_your_active_cases(admin_client, admin_user):
    """Check dashboard shows correct number of your active cases"""

    # Creates unassigned case
    create_case()
    create_case()

    # Case assigned to you
    create_case(auditor=admin_user)

    response: HttpResponse = admin_client.get(reverse("dashboard:home"))
    assert Case.objects.all().count() == 3
    assert response.status_code == 200
    expected_number_of_your_active_cases: str = """
    <div class="govuk-body-m"> Your active cases </div>
    <div class="govuk-heading-xl amp-margin-bottom-0"> 1 </div>
    """
    assertContains(
        response,
        expected_number_of_your_active_cases,
        html=True,
    )

    expected_number_of_unnassigned_cases: str = """
    <div class="govuk-body-m"> Unassigned cases </div>
    <div class="govuk-heading-xl amp-margin-bottom-0"> 2 </div>
    """
    assertContains(
        response,
        expected_number_of_unnassigned_cases,
        html=True,
    )
