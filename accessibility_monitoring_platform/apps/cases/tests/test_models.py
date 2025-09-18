"""
Tests for cases models
"""

from datetime import date, datetime

import pytest
from django.contrib.auth.models import User
from django.db.models.query import QuerySet

from ...comments.models import Comment
from ...detailed.models import DetailedCase
from ...mobile.models import MobileCase
from ...notifications.models import Task
from ...simplified.models import SimplifiedCase
from ..models import (
    ALL_CASE_STATUS_CHOICES,
    BaseCase,
    CaseStatusChoice,
    CaseStatusChoices,
    DetailedCaseStatus,
    MobileCaseStatus,
    SimplifiedCaseStatus,
    TestType,
)

REMINDER_DUE_DATE: date = date(2022, 1, 1)


def test_case_status_choice_all_choices_label():
    """
    When list all status choices add indication to label when choice is not
    available for all testing types.
    """
    case_status_choice: CaseStatusChoice = CaseStatusChoice(
        name="STATUS",
        value="990-status",
        label="Status label",
        test_types=[TestType.SIMPLIFIED],
    )

    assert case_status_choice.search_cases_choices_label == "Status label (S)"

    case_status_choice.test_types = [
        TestType.SIMPLIFIED,
        TestType.DETAILED,
        TestType.MOBILE,
    ]

    assert case_status_choice.search_cases_choices_label == "Status label"

    case_status_choice.test_types = [TestType.DETAILED, TestType.MOBILE]

    assert case_status_choice.search_cases_choices_label == "Status label (D&M)"


def test_all_case_statuses():
    """Check how many status choices there are"""
    assert len(ALL_CASE_STATUS_CHOICES) == 24


@pytest.mark.parametrize(
    "test_type, expected_number_of_choices, expected_attr",
    [
        (BaseCase.TestType.SIMPLIFIED, 17, "QA_IN_PROGRESS"),
        (BaseCase.TestType.DETAILED, 19, "PSB_INFO_REQ"),
        (BaseCase.TestType.MOBILE, 16, "UNASSIGNED"),
    ],
)
def test_case_status_choices(test_type, expected_number_of_choices, expected_attr):
    """
    Test CaseStatusChoices creates an object with statuses for a specific
    testing type.
    """
    case_status_choices: CaseStatusChoices = CaseStatusChoices(test_type=test_type)

    assert len(case_status_choices.choices) == expected_number_of_choices
    assert hasattr(case_status_choices, expected_attr) is True


def test_simplified_case_statuses():
    """Check the SimplifiedCaseStatus.choices"""

    assert SimplifiedCaseStatus.choices == [
        ("000-unassigned-case", "Unassigned case"),
        ("050-test-in-progress", "Test in progress"),
        ("060-report-in-progress", "Report in progress"),
        ("070-unassigned-qa-case", "Report ready to QA"),
        ("080-qa-in-progress", "QA in progress"),
        ("090-report-ready-to-send", "Report ready to send"),
        ("100-in-report-correspondence", "Report sent"),
        ("120-in-12-week-period", "Report acknowledged waiting for 12-week deadline"),
        ("140-after-12-week-correspondence", "After 12-week correspondence"),
        ("150-reviewing-changes", "Reviewing changes"),
        ("160-final-decision-due", "Final decision due"),
        (
            "170-case-closed-waiting-to-be-sent",
            "Case closed and waiting to be sent to equalities body",
        ),
        (
            "180-case-closed-sent-to-equalities-body",
            "Case closed and sent to equalities body",
        ),
        (
            "190-in-correspondence-with-equalities-body",
            "In correspondence with equalities body",
        ),
        ("200-complete", "Complete"),
        ("900-deactivated", "Deactivated"),
        ("910-unknown", "Unknown"),
    ]


def test_detailed_case_statuses():
    """Check the DetailedCaseStatus.choices"""
    assert DetailedCaseStatus.choices == [
        ("000-unassigned-case", "Unassigned case"),
        ("010-initial-psb-info-requested", "Requested information"),
        ("020-initial-psb-info-chasing", "Chasing initial response"),
        ("030-initial-psb-info-req-ack", "Acknowledge our request"),
        ("040-initial-psb-info-received", "Received details and access"),
        ("050-test-in-progress", "Test in progress"),
        ("060-report-in-progress", "Report in progress"),
        ("070-unassigned-qa-case", "Report ready to QA"),
        ("090-report-ready-to-send", "Report ready to send"),
        ("100-in-report-correspondence", "Report sent"),
        ("110-awaiting-report-ack", "Waiting for response"),
        ("120-in-12-week-period", "Report acknowledged waiting for 12-week deadline"),
        ("130-12-week-requested-update", "Requested update at 12 weeks"),
        ("140-after-12-week-correspondence", "After 12-week correspondence"),
        ("150-reviewing-changes", "Reviewing changes"),
        (
            "170-case-closed-waiting-to-be-sent",
            "Case closed and waiting to be sent to equalities body",
        ),
        (
            "180-case-closed-sent-to-equalities-body",
            "Case closed and sent to equalities body",
        ),
        ("200-complete", "Complete"),
        ("210-blocked", "Blocked"),
    ]


def test_mobile_case_statuses():
    """Check the MobileCaseStatus.choices"""
    assert MobileCaseStatus.choices == [
        ("000-unassigned-case", "Unassigned case"),
        ("010-initial-psb-info-requested", "Requested information"),
        ("020-initial-psb-info-chasing", "Chasing initial response"),
        ("030-initial-psb-info-req-ack", "Acknowledge our request"),
        ("040-initial-psb-info-received", "Received details and access"),
        ("050-test-in-progress", "Test in progress"),
        ("060-report-in-progress", "Report in progress"),
        ("070-unassigned-qa-case", "Report ready to QA"),
        ("090-report-ready-to-send", "Report ready to send"),
        ("100-in-report-correspondence", "Report sent"),
        ("120-in-12-week-period", "Report acknowledged waiting for 12-week deadline"),
        ("140-after-12-week-correspondence", "After 12-week correspondence"),
        ("150-reviewing-changes", "Reviewing changes"),
        (
            "170-case-closed-waiting-to-be-sent",
            "Case closed and waiting to be sent to equalities body",
        ),
        (
            "180-case-closed-sent-to-equalities-body",
            "Case closed and sent to equalities body",
        ),
        ("200-complete", "Complete"),
    ]


@pytest.mark.django_db
def test_case_identifier():
    """Test the Case.case_identifier"""
    base_case: BaseCase = BaseCase.objects.create()

    assert base_case.case_identifier == "#S-1"


@pytest.mark.django_db
def test_base_case_save_increments_version():
    """Test that saving a BaseCase increments its version"""
    base_case: BaseCase = BaseCase.objects.create()
    old_version: int = base_case.version
    base_case.save()

    assert base_case.version == old_version + 1


@pytest.mark.django_db
def test_new_base_case_defaults():
    """Test the default values of new BaseCase"""
    BaseCase.objects.create()
    base_case: BaseCase = BaseCase.objects.create(
        organisation_name="Org Name",
    )

    assert base_case.created is not None
    assert isinstance(base_case.created, datetime)
    assert base_case.created == base_case.updated
    assert base_case.updated_date == base_case.updated.date()
    assert base_case.case_number == 2
    assert base_case.case_identifier == "#S-2"
    assert base_case.get_absolute_url() == "/simplified/2/view/"
    assert str(base_case) == "Org Name | #S-2"


@pytest.mark.django_db
def test_case_reminder():
    """Test BaseCase.reminder returns the unread reminder"""
    user: User = User.objects.create()
    base_case: BaseCase = BaseCase.objects.create()
    reminder: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        base_case=base_case,
        user=user,
        date=REMINDER_DUE_DATE,
    )

    assert base_case.reminder == reminder

    reminder.read = True
    reminder.save()

    assert base_case.reminder is None


@pytest.mark.django_db
def test_case_reminder_history():
    """Test BaseCase.reminder_history returns the read reminders"""
    user: User = User.objects.create()
    base_case: BaseCase = BaseCase.objects.create()
    reminder: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        base_case=base_case,
        user=user,
        date=REMINDER_DUE_DATE,
    )

    assert base_case.reminder_history.count() == 0

    reminder.read = True
    reminder.save()

    assert base_case.reminder_history.count() == 1
    assert base_case.reminder_history.first() == reminder


@pytest.mark.django_db
def test_qa_comments():
    """
    Test the QA comments are returned in most recently created order
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Comment.objects.create(base_case=simplified_case, hidden=True)
    comment1: Comment = Comment.objects.create(base_case=simplified_case)
    comment2: Comment = Comment.objects.create(base_case=simplified_case)

    comments: QuerySet[Comment] = simplified_case.qa_comments

    assert comments.count() == 2
    assert comments[0].id == comment2.id
    assert comments[1].id == comment1.id


@pytest.mark.django_db
def test_qa_comments_count():
    """Test the QA comments count"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Comment.objects.create(base_case=simplified_case, hidden=True)
    Comment.objects.create(base_case=simplified_case)
    Comment.objects.create(base_case=simplified_case)

    assert simplified_case.qa_comments_count == 2


@pytest.mark.django_db
def test_case_get_case():
    """Test the BaseCase.get_case returns the correct subclass object"""
    detailed_case: DetailedCase = DetailedCase.objects.create()

    assert isinstance(detailed_case.get_case(), DetailedCase) is True

    mobile_case: MobileCase = MobileCase.objects.create()

    assert isinstance(mobile_case.get_case(), MobileCase) is True

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert isinstance(simplified_case.get_case(), SimplifiedCase) is True
