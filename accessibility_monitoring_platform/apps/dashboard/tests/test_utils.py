"""Test dashboard utility functions"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Union

from django.contrib.auth.models import User
from django.utils import timezone

from ...cases.models import Case

from ..utils import (
    group_cases_by_status,
    group_cases_by_qa_status,
    return_cases_requiring_user_review,
    return_recently_completed_cases,
)

FIRST_DATE = date(2021, 1, 1)
SECOND_DATE = date(2021, 2, 1)


@dataclass
class MockCase:
    """Mock of case for testing"""

    id: int
    status: str = "unknown"
    qa_status: str = "unknown"
    report_sent_date: Union[date, None] = None
    report_followup_week_12_due_date: Union[date, None] = None
    reviewer: Union[User, str, None] = None
    completed_date: Union[date, None] = None
    next_action_due_date: Union[date, None] = None


MOCK_CASES: List[MockCase] = [
    MockCase(
        id=30,
        status="qa-in-progress",
    ),
    MockCase(
        id=29,
        qa_status="in-qa",
    ),
    MockCase(
        id=28,
        qa_status="in-qa",
    ),
    MockCase(
        id=27,
        qa_status="unassigned-qa-case",
    ),
    MockCase(
        id=26,
        qa_status="unassigned-qa-case",
    ),
    MockCase(
        id=25,
        status="in-correspondence-with-equalities-body",
        report_followup_week_12_due_date=SECOND_DATE,
    ),
    MockCase(
        id=24,
        status="in-correspondence-with-equalities-body",
        report_followup_week_12_due_date=FIRST_DATE,
    ),
    MockCase(id=23, status="in-correspondence-with-equalities-body"),
    MockCase(
        id=22, status="final-decision-due", report_followup_week_12_due_date=SECOND_DATE
    ),
    MockCase(
        id=21, status="final-decision-due", report_followup_week_12_due_date=FIRST_DATE
    ),
    MockCase(id=20, status="final-decision-due"),
    MockCase(
        id=19,
        status="in-12-week-correspondence",
        next_action_due_date=SECOND_DATE,
    ),
    MockCase(
        id=18,
        status="in-12-week-correspondence",
        next_action_due_date=FIRST_DATE,
    ),
    MockCase(id=17, status="in-12-week-correspondence"),
    MockCase(
        id=16,
        status="in-probation-period",
        next_action_due_date=SECOND_DATE,
    ),
    MockCase(id=15, status="in-probation-period", next_action_due_date=FIRST_DATE),
    MockCase(id=14, status="in-probation-period"),
    MockCase(
        id=13, status="in-report-correspondence", next_action_due_date=SECOND_DATE
    ),
    MockCase(id=12, status="in-report-correspondence", next_action_due_date=FIRST_DATE),
    MockCase(id=11, status="in-report-correspondence"),
    MockCase(id=10, status="report-ready-to-send"),
    MockCase(id=9, status="report-ready-to-send"),
    MockCase(id=8, status="report-in-progress"),
    MockCase(id=7, status="report-in-progress"),
    MockCase(id=6, status="test-in-progress"),
    MockCase(id=5, status="test-in-progress"),
    MockCase(id=4, status="unassigned-case"),
    MockCase(id=3, status="unassigned-case"),
    MockCase(id=2),
    MockCase(id=1),
]

EXPECTED_MOCK_CASES_BY_STATUS = {
    "final_decision_due": [
        MockCase(
            id=21,
            status="final-decision-due",
            report_followup_week_12_due_date=date(2021, 1, 1),
        ),
        MockCase(
            id=22,
            status="final-decision-due",
            report_followup_week_12_due_date=date(2021, 2, 1),
        ),
        MockCase(id=20, status="final-decision-due"),
    ],
    "in_12_week_correspondence": [
        MockCase(
            id=18,
            status="in-12-week-correspondence",
            next_action_due_date=date(2021, 1, 1),
        ),
        MockCase(
            id=19,
            status="in-12-week-correspondence",
            next_action_due_date=date(2021, 2, 1),
        ),
        MockCase(id=17, status="in-12-week-correspondence"),
    ],
    "in_correspondence_with_equalities_body": [
        MockCase(
            id=24,
            status="in-correspondence-with-equalities-body",
            report_followup_week_12_due_date=date(2021, 1, 1),
        ),
        MockCase(
            id=25,
            status="in-correspondence-with-equalities-body",
            report_followup_week_12_due_date=date(2021, 2, 1),
        ),
        MockCase(id=23, status="in-correspondence-with-equalities-body"),
    ],
    "in_probation_period": [
        MockCase(
            id=15,
            status="in-probation-period",
            next_action_due_date=date(2021, 1, 1),
        ),
        MockCase(
            id=16,
            status="in-probation-period",
            next_action_due_date=date(2021, 2, 1),
        ),
        MockCase(id=14, status="in-probation-period"),
    ],
    "in_report_correspondence": [
        MockCase(
            id=12,
            status="in-report-correspondence",
            next_action_due_date=date(2021, 1, 1),
        ),
        MockCase(
            id=13,
            status="in-report-correspondence",
            next_action_due_date=date(2021, 2, 1),
        ),
        MockCase(id=11, status="in-report-correspondence"),
    ],
    "report_ready_to_send": [
        MockCase(id=9, status="report-ready-to-send"),
        MockCase(id=10, status="report-ready-to-send"),
    ],
    "reports_in_progress": [
        MockCase(id=7, status="report-in-progress"),
        MockCase(id=8, status="report-in-progress"),
    ],
    "qa_in_progress": [
        MockCase(id=30, status="qa-in-progress"),
    ],
    "test_in_progress": [
        MockCase(id=5, status="test-in-progress"),
        MockCase(id=6, status="test-in-progress"),
    ],
    "unassigned_cases": [
        MockCase(id=3, status="unassigned-case"),
        MockCase(id=4, status="unassigned-case"),
    ],
    "unknown": [
        MockCase(id=1),
        MockCase(id=2),
        MockCase(id=26, qa_status="unassigned-qa-case"),
        MockCase(id=27, qa_status="unassigned-qa-case"),
        MockCase(id=28, qa_status="in-qa"),
        MockCase(id=29, qa_status="in-qa"),
    ],
}

EXPECTED_MOCK_CASES_BY_QA_STATUS = {
    "ready_for_qa": [
        MockCase(id=26, qa_status="unassigned-qa-case"),
        MockCase(id=27, qa_status="unassigned-qa-case"),
    ],
}


def test_group_cases_by_status():
    """Test cases are grouped by status and sorted"""
    assert group_cases_by_status(cases=MOCK_CASES) == EXPECTED_MOCK_CASES_BY_STATUS  # type: ignore


def test_group_cases_by_qa_status():
    """Test cases are grouped by qa_status and sorted"""
    assert (
        group_cases_by_qa_status(cases=MOCK_CASES) == EXPECTED_MOCK_CASES_BY_QA_STATUS  # type: ignore
    )


def test_return_cases_requiring_user_review():
    """Test cases in QA for a specific user are returned"""
    user: User = User.objects.create()

    mock_case_1: MockCase = MockCase(id=1, reviewer=user, qa_status="in-qa")
    mock_case_2: MockCase = MockCase(id=2, reviewer=user, qa_status="in-qa")
    all_cases: List[Case] = [  # type: ignore
        mock_case_2,
        MockCase(id=3),
        mock_case_1,
    ]
    expected_cases = [mock_case_1, mock_case_2]
    assert (
        return_cases_requiring_user_review(cases=all_cases, user=user) == expected_cases
    )


def test_return_recently_completed_cases():
    """Test completed cases, compled in the last 30 days"""
    twenty_eight_days_ago: datetime = timezone.now() - timedelta(28)
    twenty_nine_days_ago: datetime = timezone.now() - timedelta(29)
    thirty_one_days_ago: datetime = timezone.now() - timedelta(31)

    mock_case_1: MockCase = MockCase(
        id=1, completed_date=twenty_nine_days_ago, status="complete"
    )
    mock_case_2: MockCase = MockCase(
        id=2, completed_date=twenty_eight_days_ago, status="complete"
    )
    all_cases: List[Case] = [  # type: ignore
        mock_case_2,
        MockCase(id=3, completed_date=thirty_one_days_ago, status="complete"),
        mock_case_1,
    ]
    expected_cases = [mock_case_1, mock_case_2]
    assert return_recently_completed_cases(cases=all_cases) == expected_cases
