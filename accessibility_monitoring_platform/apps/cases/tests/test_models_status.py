"""
Tests for automated statuses
"""
import pytest

from datetime import datetime

from django.contrib.auth.models import User

from ..models import (
    Case,
    ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
    IS_WEBSITE_COMPLIANT_COMPLIANT,
    REPORT_READY_TO_REVIEW,
    REPORT_APPROVED_STATUS_APPROVED,
    CASE_COMPLETED_SEND,
    CASE_COMPLETED_NO_SEND,
    ENFORCEMENT_BODY_PURSUING_YES_IN_PROGRESS,
    ENFORCEMENT_BODY_PURSUING_YES_COMPLETED,
    BOOLEAN_TRUE,
)


@pytest.mark.django_db
def test_case_status_deactivated():
    """Test case status returns deactivated"""
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        is_deactivated=True,
    )
    assert case.status == "deactivated"


@pytest.mark.django_db
def test_case_status_unassigned():
    """Test case status returns unassigned-case"""
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    assert case.status == "unassigned-case"


@pytest.mark.django_db
def test_case_status_test_in_progress():
    """Test case status returns test-in-progress"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
    )
    assert case.status == "test-in-progress"


@pytest.mark.django_db
def test_case_status_report_in_progress():
    """Test case status returns report-in-progress"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
    )
    assert case.status == "report-in-progress"


@pytest.mark.django_db
def test_case_status_qa_in_progress():
    """Test case status returns qa-in-progress"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        report_review_status=REPORT_READY_TO_REVIEW,
    )
    assert case.status == "qa-in-progress"


@pytest.mark.django_db
def test_case_status_report_ready_to_send():
    """Test case status returns report-ready-to-send"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        report_review_status=REPORT_READY_TO_REVIEW,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
    )
    assert case.status == "report-ready-to-send"


@pytest.mark.django_db
def test_case_status_in_report_correspondence():
    """Test case status returns in-report-correspondence"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        report_review_status=REPORT_READY_TO_REVIEW,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
    )
    assert case.status == "in-report-correspondence"


@pytest.mark.django_db
def test_case_status_in_probation_period():
    """Test case status returns in-probation-period"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        report_review_status=REPORT_READY_TO_REVIEW,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
    )
    assert case.status == "in-probation-period"


@pytest.mark.django_db
def test_case_status_in_12_week_correspondence():
    """Test case status returns in-12-week-correspondence"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        report_review_status=REPORT_READY_TO_REVIEW,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
    )
    assert case.status == "in-12-week-correspondence"


@pytest.mark.django_db
def test_case_status_reviewing_changes():
    """Test case status returns reviewing-changes"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        report_review_status=REPORT_READY_TO_REVIEW,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
    )
    assert case.status == "reviewing-changes"


@pytest.mark.django_db
def test_case_status_final_decision_due():
    """Test case status returns final-decision-due"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        report_review_status=REPORT_READY_TO_REVIEW,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        is_ready_for_final_decision=BOOLEAN_TRUE,
    )
    assert case.status == "final-decision-due"


@pytest.mark.django_db
def test_case_status_case_closed_waiting_to_be_sent():
    """Test case status returns case-closed-waiting-to-be-sent"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        report_review_status=REPORT_READY_TO_REVIEW,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        case_completed=CASE_COMPLETED_SEND,
    )
    assert case.status == "case-closed-waiting-to-be-sent"


@pytest.mark.django_db
def test_case_status_case_closed_sent_to_equality_bodies():
    """Test case status returns case-closed-sent-to-equalities-body"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
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
    assert case.status == "case-closed-sent-to-equalities-body"


@pytest.mark.django_db
def test_case_status_in_correspondence_with_equalities_body():
    """Test case status returns in-correspondence-with-equalities-body"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
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
        enforcement_body_pursuing=ENFORCEMENT_BODY_PURSUING_YES_IN_PROGRESS,
    )
    assert case.status == "in-correspondence-with-equalities-body"


@pytest.mark.django_db
def test_case_status_equality_bodies_complete():
    """Test case status returns complete"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
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
        enforcement_body_pursuing=ENFORCEMENT_BODY_PURSUING_YES_COMPLETED,
    )
    assert case.status == "complete"


@pytest.mark.django_db
def test_case_status_complete():
    """Test case status returns complete when case is exempt"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        case_completed=CASE_COMPLETED_NO_SEND,
    )
    assert case.status == "complete"


@pytest.mark.django_db
def test_case_qa_status_unassigned_qa_case():
    """Test case returns unassigned-qa-case for qa_status"""
    user = User.objects.create()
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        report_review_status=REPORT_READY_TO_REVIEW,
    )
    assert case.qa_status == "unassigned-qa-case"


@pytest.mark.django_db
def test_case_qa_status_in_qa():
    """Test case returns in-qa for qa_status"""
    user = User.objects.create(username="1")
    user2 = User.objects.create(username="2")
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        report_review_status=REPORT_READY_TO_REVIEW,
        reviewer=user2,
    )
    assert case.qa_status == "in-qa"


@pytest.mark.django_db
def test_case_qa_status_qa_approved():
    """Test case returns qa-approved for qa_status"""
    user = User.objects.create(username="1")
    user2 = User.objects.create(username="2")
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        is_website_compliant=IS_WEBSITE_COMPLIANT_COMPLIANT,
        report_review_status=REPORT_READY_TO_REVIEW,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        reviewer=user2,
    )
    assert case.qa_status == "qa-approved"
