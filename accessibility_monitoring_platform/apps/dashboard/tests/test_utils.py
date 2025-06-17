"""Test dashboard utility functions"""

from dataclasses import dataclass
from datetime import date

from django.contrib.auth.models import User

from ..utils import (
    get_all_cases_in_qa,
    group_cases_by_status,
    return_cases_requiring_user_review,
)

FIRST_DATE = date(2021, 1, 1)
SECOND_DATE = date(2021, 2, 1)


@dataclass
class MockCase:
    """Mock of case for testing"""

    id: int
    status: str = "unassigned-case"
    qa_status: str = "unknown"
    report_sent_date: date | None = None
    report_followup_week_12_due_date: date | None = None
    reviewer: User | str | None = None
    completed_date: date | None = None
    next_action_due_date: date | None = None
    twelve_week_correspondence_acknowledged_date: date | None = None
    case_close_complete_date: date | None = None
    sent_to_enforcement_body_sent_date: date | None = None


MOCK_CASES: list[MockCase] = [
    MockCase(
        id=33,
        status="reviewing-changes",
        twelve_week_correspondence_acknowledged_date=FIRST_DATE,
    ),
    MockCase(
        id=32,
        status="case-closed-sent-to-equalities-body",
        sent_to_enforcement_body_sent_date=FIRST_DATE,
    ),
    MockCase(
        id=31,
        status="case-closed-waiting-to-be-sent",
        case_close_complete_date=FIRST_DATE,
    ),
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
        status="qa-in-progress",
    ),
    MockCase(
        id=26,
        status="qa-in-progress",
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
    MockCase(
        id=23,
        status="in-correspondence-with-equalities-body",
    ),
    MockCase(
        id=22,
        status="final-decision-due",
        report_followup_week_12_due_date=SECOND_DATE,
    ),
    MockCase(
        id=21,
        status="final-decision-due",
        report_followup_week_12_due_date=FIRST_DATE,
    ),
    MockCase(
        id=20,
        status="final-decision-due",
    ),
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
    MockCase(
        id=17,
        status="in-12-week-correspondence",
    ),
    MockCase(
        id=16,
        status="in-probation-period",
        next_action_due_date=SECOND_DATE,
    ),
    MockCase(
        id=15,
        status="in-probation-period",
        next_action_due_date=FIRST_DATE,
    ),
    MockCase(
        id=14,
        status="in-probation-period",
    ),
    MockCase(
        id=13,
        status="in-report-correspondence",
        next_action_due_date=SECOND_DATE,
    ),
    MockCase(
        id=12,
        status="in-report-correspondence",
        next_action_due_date=FIRST_DATE,
    ),
    MockCase(
        id=11,
        status="in-report-correspondence",
    ),
    MockCase(
        id=10,
        status="report-ready-to-send",
    ),
    MockCase(
        id=9,
        status="report-ready-to-send",
    ),
    MockCase(
        id=8,
        status="report-in-progress",
    ),
    MockCase(
        id=7,
        status="report-in-progress",
    ),
    MockCase(
        id=6,
        status="test-in-progress",
    ),
    MockCase(
        id=5,
        status="test-in-progress",
    ),
    MockCase(
        id=4,
        status="unassigned-case",
    ),
    MockCase(
        id=3,
        status="unassigned-case",
    ),
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
        MockCase(
            id=20,
            status="final-decision-due",
        ),
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
        MockCase(
            id=17,
            status="in-12-week-correspondence",
        ),
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
        MockCase(
            id=23,
            status="in-correspondence-with-equalities-body",
        ),
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
        MockCase(
            id=14,
            status="in-probation-period",
        ),
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
        MockCase(
            id=9,
            status="report-ready-to-send",
        ),
        MockCase(
            id=10,
            status="report-ready-to-send",
        ),
    ],
    "reports_in_progress": [
        MockCase(
            id=7,
            status="report-in-progress",
        ),
        MockCase(
            id=8,
            status="report-in-progress",
        ),
    ],
    "qa_in_progress": [
        MockCase(
            id=26,
            status="qa-in-progress",
        ),
        MockCase(
            id=27,
            status="qa-in-progress",
        ),
        MockCase(
            id=30,
            status="qa-in-progress",
        ),
    ],
    "test_in_progress": [
        MockCase(
            id=5,
            status="test-in-progress",
        ),
        MockCase(
            id=6,
            status="test-in-progress",
        ),
    ],
    "unknown": [],
    "unassigned-case": [
        MockCase(id=1),
        MockCase(id=2),
        MockCase(
            id=3,
            status="unassigned-case",
        ),
        MockCase(
            id=4,
            status="unassigned-case",
        ),
        MockCase(
            id=28,
            qa_status="in-qa",
        ),
        MockCase(
            id=29,
            qa_status="in-qa",
        ),
    ],
    "case_closed_waiting_to_be_sent": [
        MockCase(
            id=31,
            status="case-closed-waiting-to-be-sent",
            case_close_complete_date=FIRST_DATE,
        ),
    ],
    "case_closed_sent_to_equalities_body": [
        MockCase(
            id=32,
            status="case-closed-sent-to-equalities-body",
            sent_to_enforcement_body_sent_date=FIRST_DATE,
        ),
    ],
    "reviewing_changes": [
        MockCase(
            id=33,
            status="reviewing-changes",
            twelve_week_correspondence_acknowledged_date=FIRST_DATE,
        ),
    ],
    "completed": [],
}

EXPECTED_MOCK_CASES_IN_QA = [
    MockCase(
        id=26,
        status="qa-in-progress",
    ),
    MockCase(
        id=27,
        status="qa-in-progress",
    ),
    MockCase(
        id=30,
        status="qa-in-progress",
    ),
]


def test_group_cases_by_status():
    """Test cases are grouped by status and sorted"""
    assert group_cases_by_status(simplified_cases=MOCK_CASES) == EXPECTED_MOCK_CASES_BY_STATUS  # type: ignore


def test_get_all_cases_in_qa():
    """Test cases in qa are sorted and returned"""
    assert get_all_cases_in_qa(all_cases=MOCK_CASES) == EXPECTED_MOCK_CASES_IN_QA  # type: ignore


def test_return_cases_requiring_user_review():
    """Test cases in QA for a specific user are returned"""
    user: User = User()

    mock_case_1: MockCase = MockCase(
        id=1,
        reviewer=user,
        qa_status="in-qa",
    )
    mock_case_2: MockCase = MockCase(
        id=2,
        reviewer=user,
        qa_status="in-qa",
    )
    all_cases: list[MockCase] = [  # type: ignore
        mock_case_2,
        MockCase(id=3),
        mock_case_1,
    ]
    expected_cases = [mock_case_1, mock_case_2]
    assert (
        return_cases_requiring_user_review(simplified_cases=all_cases, user=user)
        == expected_cases
    )
