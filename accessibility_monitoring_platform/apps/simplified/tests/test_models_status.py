"""
Tests for automated statuses
"""

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains

from ..models import Boolean, CaseCompliance, CaseStatus, SimplifiedCase
from ..utils import create_case_and_compliance


def check_for_status_specific_link(
    admin_client, simplified_case: SimplifiedCase, expected_link_label: str
):
    response: HttpResponse = admin_client.get(
        reverse("simplified:case-detail", kwargs={"pk": simplified_case.id}),
    )
    assert response.status_code == 200
    assertContains(response, expected_link_label)


def test_case_status_deactivated(admin_client):
    """Test case status returns deactivated"""
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        is_deactivated=True,
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.DEACTIVATED

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to case metadata",
    )


def test_case_status_unassigned(admin_client):
    """Test case status returns unassigned-case"""
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.UNASSIGNED

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to case metadata",
    )


def test_case_status_test_in_progress(admin_client):
    """Test case status returns test-in-progress"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.TEST_IN_PROGRESS

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to testing details",
    )


def test_case_status_report_in_progress(admin_client):
    """Test case status returns report-in-progress"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.REPORT_IN_PROGRESS

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to report ready for QA",
    )


def test_case_status_qa_in_progress(admin_client):
    """Test case status returns qa-in-progress"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.QA_IN_PROGRESS

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to QA approval",
    )


def test_case_status_report_ready_to_send(admin_client):
    """Test case status returns report-ready-to-send"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.REPORT_READY_TO_SEND

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to Report sent on",
    )


def test_case_status_in_report_correspondence(admin_client):
    """Test case status returns in-report-correspondence"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
        report_sent_date=date.today(),
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.IN_REPORT_CORES

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label=simplified_case.in_report_correspondence_progress.label,
    )


def test_case_status_when_no_psb_contact(admin_client):
    """Test case status returns final-decision-due"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
        no_psb_contact=Boolean.YES,
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.FINAL_DECISION_DUE

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Closing the case",
    )


def test_case_status_in_probation_period(admin_client):
    """Test case status returns in-probation-period"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.AWAITING_12_WEEK_DEADLINE

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to 12-week update requested",
    )


def test_case_status_in_12_week_correspondence(admin_client):
    """Test case status returns in-12-week-correspondence"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.IN_12_WEEK_CORES

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label=simplified_case.twelve_week_correspondence_progress.label,
    )


def test_case_status_skips_to_reviewing_changes_when_psb_respond_early(admin_client):
    """Test case status returns in-12-week-correspondence"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.REVIEWING_CHANGES

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to reviewing changes",
    )


def test_case_status_reviewing_changes(admin_client):
    """Test case status returns reviewing-changes"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.REVIEWING_CHANGES

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to reviewing changes",
    )


def test_case_status_final_decision_due(admin_client):
    """Test case status returns final-decision-due"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
        is_ready_for_final_decision=Boolean.YES,
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.FINAL_DECISION_DUE

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to closing the case",
    )


def test_case_status_case_closed_waiting_to_be_sent(admin_client):
    """Test case status returns case-closed-waiting-to-be-sent"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
        case_completed=SimplifiedCase.CaseCompleted.COMPLETE_SEND,
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.CASE_CLOSED_WAITING_TO_SEND

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to closing the case",
    )


def test_case_status_case_closed_sent_to_equality_bodies(admin_client):
    """Test case status returns case-closed-sent-to-equalities-body"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
        case_completed=SimplifiedCase.CaseCompleted.COMPLETE_SEND,
        sent_to_enforcement_body_sent_date=date.today(),
    )
    simplified_case.update_case_status()

    assert (
        simplified_case.status
        == SimplifiedCase.Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY
    )

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to equality body metadata",
    )


def test_case_status_in_correspondence_with_equalities_body(admin_client):
    """Test case status returns in-correspondence-with-equalities-body"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
        case_completed=SimplifiedCase.CaseCompleted.COMPLETE_SEND,
        sent_to_enforcement_body_sent_date=date.today(),
        enforcement_body_pursuing=SimplifiedCase.EnforcementBodyPursuing.YES_IN_PROGRESS,
    )
    simplified_case.update_case_status()

    assert (
        simplified_case.status == SimplifiedCase.Status.IN_CORES_WITH_ENFORCEMENT_BODY
    )

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to equality body metadata",
    )


def test_case_status_equality_bodies_complete(admin_client):
    """Test case status returns complete"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
        report_sent_date=date.today(),
        report_acknowledged_date=date.today(),
        twelve_week_update_requested_date=date.today(),
        twelve_week_correspondence_acknowledged_date=date.today(),
        case_completed=SimplifiedCase.CaseCompleted.COMPLETE_SEND,
        sent_to_enforcement_body_sent_date=date.today(),
        enforcement_body_pursuing=SimplifiedCase.EnforcementBodyPursuing.YES_COMPLETED,
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.COMPLETE

    check_for_status_specific_link(
        admin_client,
        simplified_case=simplified_case,
        expected_link_label="Go to post case summary",
    )


@pytest.mark.django_db
def test_case_status_complete():
    """Test case status returns complete when case is exempt"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        case_completed=SimplifiedCase.CaseCompleted.COMPLETE_NO_SEND,
    )
    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.COMPLETE


@pytest.mark.django_db
def test_case_qa_status_unassigned_qa_case():
    """Test case returns unassigned-qa-case for qa_status"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
    )
    simplified_case.update_case_status()

    assert simplified_case.qa_status == SimplifiedCase.QAStatus.UNASSIGNED


@pytest.mark.django_db
def test_case_qa_status_in_qa():
    """Test case returns in-qa for qa_status"""
    user: User = User.objects.create(username="1")
    user2: User = User.objects.create(username="2")
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        reviewer=user2,
    )
    simplified_case.update_case_status()

    assert simplified_case.qa_status == SimplifiedCase.QAStatus.IN_QA


@pytest.mark.django_db
def test_case_qa_status_qa_approved():
    """Test case returns qa-approved for qa_status"""
    user: User = User.objects.create(username="1")
    user2: User = User.objects.create(username="2")
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
        reviewer=user2,
    )
    simplified_case.update_case_status()

    assert simplified_case.qa_status == SimplifiedCase.QAStatus.APPROVED
