"""
Tests for automated statuses
"""
from datetime import datetime
import pytest
from ..models import Case
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_case_status_unassigned():
    """Test case returns unassigned-case for status"""
    case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
    )
    assert case.status == "unassigned-case"


@pytest.mark.django_db
def test_case_status_test_in_progress():
    """Test case returns test-in-progress for status"""
    user = User.objects.create()
    case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
    )
    case.save()
    assert case.status == "test-in-progress"


@pytest.mark.django_db
def test_case_status_report_in_progress():
    """Test case returns report-in-progress for status"""
    user = User.objects.create()
    case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        test_status="complete",
    )
    case.save()
    assert case.status == "report-in-progress"


@pytest.mark.django_db
def test_case_status_qa_in_progress():
    """Test case returns qa-in-progress for status"""
    user = User.objects.create()
    case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        test_status="complete",
        report_review_status="ready-to-review",
    )
    case.save()
    assert case.status == "qa-in-progress"


@pytest.mark.django_db
def test_case_status_report_ready_to_send():
    """Test case returns report-ready-to-send for status"""
    user = User.objects.create()
    case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        test_status="complete",
        report_review_status="ready-to-review",
        report_approved_status="yes",
    )
    case.save()
    assert case.status == "report-ready-to-send"


@pytest.mark.django_db
def test_case_status_in_report_correspondence():
    """Test case returns in-report-correspondence for status"""
    user = User.objects.create()
    case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        test_status="complete",
        report_review_status="ready-to-review",
        report_approved_status="yes",
        report_sent_date=datetime.now(),
    )
    case.save()
    assert case.status == "in-report-correspondence"


@pytest.mark.django_db
def test_case_status_in_probation_period():
    """Test case returns in-probation-period for status"""
    user = User.objects.create()
    case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        test_status="complete",
        report_review_status="ready-to-review",
        report_approved_status="yes",
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
    )
    case.save()
    assert case.status == "in-probation-period"


@pytest.mark.django_db
def test_case_status_in_12_week_correspondence():
    """Test case returns in-12-week-correspondence for status"""
    user = User.objects.create()
    case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        test_status="complete",
        report_review_status="ready-to-review",
        report_approved_status="yes",
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
    )
    case.save()
    assert case.status == "in-12-week-correspondence"


@pytest.mark.django_db
def test_case_status_final_decision_due():
    """Test case returns final-decision-due for status"""
    user = User.objects.create()
    case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        test_status="complete",
        report_review_status="ready-to-review",
        report_approved_status="yes",
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
    )
    case.save()
    assert case.status == "final-decision-due"


@pytest.mark.django_db
def test_case_status_in_correspondence_with_equalities_body():
    """Test case returns in-correspondence-with-equalities-body for status"""
    user = User.objects.create()
    case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        test_status="complete",
        report_review_status="ready-to-review",
        report_approved_status="yes",
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        case_completed="escalated",
    )
    case.save()
    assert case.status == "in-correspondence-with-equalities-body"


@pytest.mark.django_db
def test_case_qa_status_unassigned_qa_case():
    """Test case returns unassigned-qa-case for qa_status"""
    user = User.objects.create()
    case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        test_status="complete",
        report_review_status="ready-to-review",
    )
    case.save()
    assert case.qa_status == "unassigned-qa-case"


@pytest.mark.django_db
def test_case_qa_status_in_qa():
    """Test case returns in-qa for qa_status"""
    user = User.objects.create(username="1")
    user2 = User.objects.create(username="2")
    case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        test_status="complete",
        report_review_status="ready-to-review",
        reviewer=user2,
    )
    case.save()
    assert case.qa_status == "in-qa"


@pytest.mark.django_db
def test_case_qa_status_qa_approved():
    """Test case returns qa-approved for qa_status"""
    user = User.objects.create(username="1")
    user2 = User.objects.create(username="2")
    case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        test_status="complete",
        report_review_status="ready-to-review",
        report_approved_status="yes",
        reviewer=user2,
    )
    case.save()
    assert case.qa_status == "qa-approved"
