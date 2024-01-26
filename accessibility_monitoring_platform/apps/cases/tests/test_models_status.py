"""
Tests for automated statuses
"""
from datetime import datetime

import pytest
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains

from ..models import Boolean, Case, CaseCompliance
from ..utils import create_case_and_compliance


def check_for_status_specific_link(admin_client, case: Case, expected_link_label: str):
    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(response, expected_link_label)


def test_case_status_deactivated(admin_client):
    """Test case status returns deactivated"""
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        is_deactivated=True,
    )
    assert case.status.status == "deactivated"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to case details"
    )


def test_case_status_unassigned(admin_client):
    """Test case status returns unassigned-case"""
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    assert case.status.status == "unassigned-case"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to case details"
    )


def test_case_status_test_in_progress(admin_client):
    """Test case status returns test-in-progress"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
    )
    assert case.status.status == "test-in-progress"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to testing details"
    )


def test_case_status_report_in_progress(admin_client):
    """Test case status returns report-in-progress"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
    )

    assert case.status.status == "report-in-progress"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to report details"
    )


def test_case_status_qa_in_progress(admin_client):
    """Test case status returns qa-in-progress"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
    )
    assert case.status.status == "qa-in-progress"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to QA auditor"
    )


def test_case_status_report_ready_to_send(admin_client):
    """Test case status returns report-ready-to-send"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
    )
    assert case.status.status == "report-ready-to-send"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to Report sent on"
    )


def test_case_status_in_report_correspondence(admin_client):
    """Test case status returns in-report-correspondence"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        report_sent_date=datetime.now(),
    )
    assert case.status.status == "in-report-correspondence"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to One week follow-up"
    )


def test_case_status_when_no_psb_contact(admin_client):
    """Test case status returns final-decision-due"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        no_psb_contact=Boolean.YES,
    )
    assert case.status.status == "final-decision-due"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Closing the case"
    )


def test_case_status_in_probation_period(admin_client):
    """Test case status returns in-probation-period"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
    )
    assert case.status.status == "in-probation-period"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to 12-week update requested"
    )


def test_case_status_in_12_week_correspondence(admin_client):
    """Test case status returns in-12-week-correspondence"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
    )
    assert case.status.status == "in-12-week-correspondence"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to 12-week update requested"
    )


def test_case_status_skips_to_reviewing_changes_when_psb_respond_early(admin_client):
    """Test case status returns in-12-week-correspondence"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
    )
    assert case.status.status == "reviewing-changes"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to reviewing changes"
    )


def test_case_status_reviewing_changes(admin_client):
    """Test case status returns reviewing-changes"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
    )
    assert case.status.status == "reviewing-changes"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to reviewing changes"
    )


def test_case_status_final_decision_due(admin_client):
    """Test case status returns final-decision-due"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        is_ready_for_final_decision=Boolean.YES,
    )
    assert case.status.status == "final-decision-due"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to closing the case"
    )


def test_case_status_case_closed_waiting_to_be_sent(admin_client):
    """Test case status returns case-closed-waiting-to-be-sent"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        case_completed=Case.CaseCompleted.COMPLETE_SEND,
    )
    assert case.status.status == "case-closed-waiting-to-be-sent"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to closing the case"
    )


def test_case_status_case_closed_sent_to_equality_bodies(admin_client):
    """Test case status returns case-closed-sent-to-equalities-body"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
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
    assert case.status.status == "case-closed-sent-to-equalities-body"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to equality body metadata"
    )


def test_case_status_in_correspondence_with_equalities_body(admin_client):
    """Test case status returns in-correspondence-with-equalities-body"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
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
        enforcement_body_pursuing=Case.EnforcementBodyPursuing.YES_IN_PROGRESS,
    )
    assert case.status.status == "in-correspondence-with-equalities-body"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to equality body metadata"
    )


def test_case_status_equality_bodies_complete(admin_client):
    """Test case status returns complete"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
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
    assert case.status.status == "complete"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to post case summary"
    )


@pytest.mark.django_db
def test_case_status_complete():
    """Test case status returns complete when case is exempt"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        case_completed=Case.CaseCompleted.COMPLETE_NO_SEND,
    )
    assert case.status.status == "complete"


@pytest.mark.django_db
def test_case_qa_status_unassigned_qa_case():
    """Test case returns unassigned-qa-case for qa_status"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
    )
    assert case.qa_status == "unassigned-qa-case"


@pytest.mark.django_db
def test_case_qa_status_in_qa():
    """Test case returns in-qa for qa_status"""
    user: User = User.objects.create(username="1")
    user2: User = User.objects.create(username="2")
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        reviewer=user2,
    )
    assert case.qa_status == "in-qa"


@pytest.mark.django_db
def test_case_qa_status_qa_approved():
    """Test case returns qa-approved for qa_status"""
    user: User = User.objects.create(username="1")
    user2: User = User.objects.create(username="2")
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        reviewer=user2,
    )
    assert case.qa_status == "qa-approved"
