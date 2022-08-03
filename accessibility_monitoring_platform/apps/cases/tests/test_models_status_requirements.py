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
    assert case.status_requirements == [
    {
        "text": "Something has gone wrong :(",
        "url": "None",
    },
]


@pytest.mark.django_db
def test_case_status_unassigned():
    """Test case status returns unassigned-case"""
    case = Case.objects.create(
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    assert case.status == "unassigned-case"
    assert case.status_requirements == [
        {
            "text": "Assign an auditor",
            "url": "cases:edit-case-details",
        },
    ]


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
    assert case.status_requirements == [
        {
            "text": "Initial compliance decision decision is not filled in",
            "url": "cases:edit-test-results",
        },
        {
            "text": "Initial accessibility statement decision is not filled in",
            "url": "cases:edit-test-results",
        }
    ]
    case.is_website_compliant = "compliant"
    case.save()
    assert case.status_requirements == [
        {
            "text": "Initial accessibility statement decision is not filled in",
            "url": "cases:edit-test-results",
        }
    ]


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
    assert case.status_requirements == [
        {
            "text": "Report ready to be reviewed needs to be Yes",
            "url": "cases:edit-qa-process",
        },
    ]


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
    assert case.status_requirements == [
        {
            "text": "Report approved needs to be Yes",
            "url": "cases:edit-qa-process",
        },
    ]


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
    assert case.status_requirements == [
        {
            "text": "Report sent on requires a date",
            "url": "cases:edit-report-correspondence",
        },
    ]


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
    assert case.status_requirements == [
        {
            "text": "Report acknowledged requires a date",
            "url": "cases:edit-report-correspondence",
        },
    ]


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
    assert case.status_requirements == [
        {
            "text": "12 week update requested requires a date",
            "url": "cases:edit-twelve-week-correspondence",
        },
    ]


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
    assert case.status_requirements == [
        {
            "text": "12 week update received requires a date or mark the case as having no response",
            "url": "cases:edit-twelve-week-correspondence",
        },
    ]


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
    assert case.status_requirements == [
        {
            "text": "Is this case ready for final decision? needs to be Yes",
            "url": "cases:edit-review-changes",
        },
    ]


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
    assert case.status_requirements == [
        {
            "text": "Case completed requires a decision",
            "url": "cases:edit-case-close",
        },
    ]


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
    assert case.status_requirements == [
        {
            "text": "Date sent to equality body requires a date",
            "url": "cases:edit-enforcement-body-correspondence",
        },
    ]


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
    assert case.status_requirements == [
        {
            # pylint: disable-next=line-too-long
            "text": "Equality body pursuing this case? should either be 'Yes, completed' or 'Yes, in progress'",
            "url": "cases:edit-enforcement-body-correspondence",
        },
    ]


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
    assert case.status_requirements == [
        {
            "text": "Equality body pursuing this case? should be 'Yes, completed'",
            "url": "cases:edit-enforcement-body-correspondence",
        }
    ]



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
    assert case.status_requirements == [
        {
            "text": "No additional requirements",
            "url": "None",
        },
    ]
