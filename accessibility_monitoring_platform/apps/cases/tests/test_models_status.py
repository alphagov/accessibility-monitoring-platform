"""
Tests for automated statuses
"""

from datetime import date

import pytest
from django.contrib.auth.models import User

from ..models import Boolean, Case, CaseCompliance, CaseStatus
from ..utils import create_case_and_compliance


def test_case_status_deactivated(admin_client):
    """Test case status returns deactivated"""
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        is_deactivated=True,
    )
    assert case.status.status == CaseStatus.Status.DEACTIVATED


def test_case_status_unassigned(admin_client):
    """Test case status returns unassigned-case"""
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    assert case.status.status == CaseStatus.Status.UNASSIGNED


def test_case_status_test_in_progress(admin_client):
    """Test case status returns test-in-progress"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
    )
    assert case.status.status == CaseStatus.Status.TEST_IN_PROGRESS


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

    assert case.status.status == CaseStatus.Status.REPORT_IN_PROGRESS


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
    assert case.status.status == CaseStatus.Status.QA_IN_PROGRESS


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
    assert case.status.status == CaseStatus.Status.REPORT_READY_TO_SEND


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
        report_sent_date=date.today(),
    )
    assert case.status.status == CaseStatus.Status.IN_REPORT_CORES


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
    assert case.status.status == CaseStatus.Status.FINAL_DECISION_DUE


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
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
    )
    assert case.status.status == CaseStatus.Status.AWAITING_12_WEEK_DEADLINE


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
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
    )
    assert case.status.status == CaseStatus.Status.IN_12_WEEK_CORES


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
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
    )
    assert case.status.status == CaseStatus.Status.REVIEWING_CHANGES


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
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
    )
    assert case.status.status == CaseStatus.Status.REVIEWING_CHANGES


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
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
        is_ready_for_final_decision=Boolean.YES,
    )
    assert case.status.status == CaseStatus.Status.FINAL_DECISION_DUE


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
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
        case_completed=Case.CaseCompleted.COMPLETE_SEND,
    )
    assert case.status.status == CaseStatus.Status.CASE_CLOSED_WAITING_TO_SEND


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
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
        case_completed=Case.CaseCompleted.COMPLETE_SEND,
        sent_to_enforcement_body_sent_date=date.today(),
    )
    assert case.status.status == CaseStatus.Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY


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
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
        case_completed=Case.CaseCompleted.COMPLETE_SEND,
        sent_to_enforcement_body_sent_date=date.today(),
        enforcement_body_pursuing=Case.EnforcementBodyPursuing.YES_IN_PROGRESS,
    )
    assert case.status.status == CaseStatus.Status.IN_CORES_WITH_ENFORCEMENT_BODY


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
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
        case_completed=Case.CaseCompleted.COMPLETE_SEND,
        sent_to_enforcement_body_sent_date=date.today(),
        enforcement_body_pursuing=Case.EnforcementBodyPursuing.YES_COMPLETED,
    )
    assert case.status.status == CaseStatus.Status.COMPLETE


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
    assert case.status.status == CaseStatus.Status.COMPLETE


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
    assert case.qa_status == Case.QAStatus.UNASSIGNED


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
    assert case.qa_status == Case.QAStatus.IN_QA


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
    assert case.qa_status == Case.QAStatus.APPROVED
