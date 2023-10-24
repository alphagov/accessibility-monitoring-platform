"""
Tests for automated statuses
"""
import pytest

from datetime import datetime
from typing import Any, Dict

from pytest_django.asserts import assertContains

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse

from ..models import (
    Case,
    CaseCompliance,
    COMPLIANCE_FIELDS,
    ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
    WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
    REPORT_APPROVED_STATUS_APPROVED,
    CASE_COMPLETED_SEND,
    CASE_COMPLETED_NO_SEND,
    ENFORCEMENT_BODY_PURSUING_YES_IN_PROGRESS,
    ENFORCEMENT_BODY_PURSUING_YES_COMPLETED,
    BOOLEAN_TRUE,
)
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
    assert case.status == "deactivated"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to case details"
    )


def test_case_status_unassigned(admin_client):
    """Test case status returns unassigned-case"""
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    assert case.status == "unassigned-case"

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
    assert case.status == "test-in-progress"

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
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
    )

    assert case.status == "report-in-progress"

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
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
    )
    assert case.status == "qa-in-progress"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to QA process"
    )


def test_case_status_report_ready_to_send(admin_client):
    """Test case status returns report-ready-to-send"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
    )
    assert case.status == "report-ready-to-send"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to contact details"
    )


def test_case_status_in_report_correspondence(admin_client):
    """Test case status returns in-report-correspondence"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
    )
    assert case.status == "in-report-correspondence"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to report correspondence"
    )


def test_case_status_when_no_psb_contact(admin_client):
    """Test case status returns final-decision-due"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        no_psb_contact=BOOLEAN_TRUE,
    )
    assert case.status == "final-decision-due"

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
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
    )
    assert case.status == "in-probation-period"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to 12-week correspondence"
    )


def test_case_status_in_12_week_correspondence(admin_client):
    """Test case status returns in-12-week-correspondence"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
    )
    assert case.status == "in-12-week-correspondence"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to 12-week correspondence"
    )


def test_case_status_reviewing_changes(admin_client):
    """Test case status returns reviewing-changes"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
    )
    assert case.status == "reviewing-changes"

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
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        is_ready_for_final_decision=BOOLEAN_TRUE,
    )
    assert case.status == "final-decision-due"

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
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        case_completed=CASE_COMPLETED_SEND,
    )
    assert case.status == "case-closed-waiting-to-be-sent"

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
    assert case.status == "case-closed-sent-to-equalities-body"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to equality body summary"
    )


def test_case_status_in_correspondence_with_equalities_body(admin_client):
    """Test case status returns in-correspondence-with-equalities-body"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
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
        enforcement_body_pursuing=ENFORCEMENT_BODY_PURSUING_YES_IN_PROGRESS,
    )
    assert case.status == "in-correspondence-with-equalities-body"

    check_for_status_specific_link(
        admin_client, case=case, expected_link_label="Go to equality body summary"
    )


def test_case_status_equality_bodies_complete(admin_client):
    """Test case status returns complete"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
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
    assert case.status == "complete"

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
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        case_completed=CASE_COMPLETED_NO_SEND,
    )
    assert case.status == "complete"


@pytest.mark.django_db
def test_case_qa_status_unassigned_qa_case():
    """Test case returns unassigned-qa-case for qa_status"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
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
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
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
        statement_compliance_state_initial=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_review_status=BOOLEAN_TRUE,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        reviewer=user2,
    )
    assert case.qa_status == "qa-approved"
