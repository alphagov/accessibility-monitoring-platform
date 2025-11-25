"""Test dashboard utility functions"""

from dataclasses import dataclass
from datetime import date

from django.contrib.auth.models import User

from ...detailed.models import DetailedCase
from ...simplified.models import SimplifiedCase
from ..utils import (
    get_all_cases_in_qa,
    group_cases_by_status,
    group_detailed_or_mobile_cases_by_status,
    return_cases_requiring_user_review,
)

FIRST_DATE = date(2021, 1, 1)
SECOND_DATE = date(2021, 2, 1)


@dataclass
class MockCase:
    """Mock of case for testing"""

    id: int
    status: str = SimplifiedCase.Status.UNASSIGNED
    qa_status: str = SimplifiedCase.QAStatus.UNKNOWN
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
        status=SimplifiedCase.Status.REVIEWING_CHANGES,
        twelve_week_correspondence_acknowledged_date=FIRST_DATE,
    ),
    MockCase(
        id=32,
        status=SimplifiedCase.Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY,
        sent_to_enforcement_body_sent_date=FIRST_DATE,
    ),
    MockCase(
        id=31,
        status=SimplifiedCase.Status.CASE_CLOSED_WAITING_TO_SEND,
        case_close_complete_date=FIRST_DATE,
    ),
    MockCase(
        id=30,
        status=SimplifiedCase.Status.QA_IN_PROGRESS,
    ),
    MockCase(
        id=29,
        qa_status=SimplifiedCase.QAStatus.IN_QA,
    ),
    MockCase(
        id=28,
        qa_status=SimplifiedCase.QAStatus.IN_QA,
    ),
    MockCase(
        id=27,
        status=SimplifiedCase.Status.QA_IN_PROGRESS,
    ),
    MockCase(
        id=26,
        status=SimplifiedCase.Status.QA_IN_PROGRESS,
    ),
    MockCase(
        id=25,
        status=SimplifiedCase.Status.IN_CORES_WITH_ENFORCEMENT_BODY,
        report_followup_week_12_due_date=SECOND_DATE,
    ),
    MockCase(
        id=24,
        status=SimplifiedCase.Status.IN_CORES_WITH_ENFORCEMENT_BODY,
        report_followup_week_12_due_date=FIRST_DATE,
    ),
    MockCase(
        id=23,
        status=SimplifiedCase.Status.IN_CORES_WITH_ENFORCEMENT_BODY,
    ),
    MockCase(
        id=22,
        status=SimplifiedCase.Status.FINAL_DECISION_DUE,
        report_followup_week_12_due_date=SECOND_DATE,
    ),
    MockCase(
        id=21,
        status=SimplifiedCase.Status.FINAL_DECISION_DUE,
        report_followup_week_12_due_date=FIRST_DATE,
    ),
    MockCase(
        id=20,
        status=SimplifiedCase.Status.FINAL_DECISION_DUE,
    ),
    MockCase(
        id=19,
        status=SimplifiedCase.Status.AFTER_12_WEEK_CORES,
        next_action_due_date=SECOND_DATE,
    ),
    MockCase(
        id=18,
        status=SimplifiedCase.Status.AFTER_12_WEEK_CORES,
        next_action_due_date=FIRST_DATE,
    ),
    MockCase(
        id=17,
        status=SimplifiedCase.Status.AFTER_12_WEEK_CORES,
    ),
    MockCase(
        id=16,
        status=SimplifiedCase.Status.AWAITING_12_WEEK_DEADLINE,
        next_action_due_date=SECOND_DATE,
    ),
    MockCase(
        id=15,
        status=SimplifiedCase.Status.AWAITING_12_WEEK_DEADLINE,
        next_action_due_date=FIRST_DATE,
    ),
    MockCase(
        id=14,
        status=SimplifiedCase.Status.AWAITING_12_WEEK_DEADLINE,
    ),
    MockCase(
        id=13,
        status=SimplifiedCase.Status.IN_REPORT_CORES,
        next_action_due_date=SECOND_DATE,
    ),
    MockCase(
        id=12,
        status=SimplifiedCase.Status.IN_REPORT_CORES,
        next_action_due_date=FIRST_DATE,
    ),
    MockCase(
        id=11,
        status=SimplifiedCase.Status.IN_REPORT_CORES,
    ),
    MockCase(
        id=10,
        status=SimplifiedCase.Status.REPORT_READY_TO_SEND,
    ),
    MockCase(
        id=9,
        status=SimplifiedCase.Status.REPORT_READY_TO_SEND,
    ),
    MockCase(
        id=8,
        status=SimplifiedCase.Status.REPORT_IN_PROGRESS,
    ),
    MockCase(
        id=7,
        status=SimplifiedCase.Status.REPORT_IN_PROGRESS,
    ),
    MockCase(
        id=6,
        status=SimplifiedCase.Status.TEST_IN_PROGRESS,
    ),
    MockCase(
        id=5,
        status=SimplifiedCase.Status.TEST_IN_PROGRESS,
    ),
    MockCase(
        id=4,
        status=SimplifiedCase.Status.UNASSIGNED,
    ),
    MockCase(
        id=3,
        status=SimplifiedCase.Status.UNASSIGNED,
    ),
    MockCase(id=2),
    MockCase(id=1),
]

EXPECTED_MOCK_CASES_BY_STATUS: dict[str, list[MockCase]] = {
    "final_decision_due": [
        MockCase(
            id=21,
            status=SimplifiedCase.Status.FINAL_DECISION_DUE,
            report_followup_week_12_due_date=date(2021, 1, 1),
        ),
        MockCase(
            id=22,
            status=SimplifiedCase.Status.FINAL_DECISION_DUE,
            report_followup_week_12_due_date=date(2021, 2, 1),
        ),
        MockCase(
            id=20,
            status=SimplifiedCase.Status.FINAL_DECISION_DUE,
        ),
    ],
    "in_12_week_correspondence": [
        MockCase(
            id=18,
            status=SimplifiedCase.Status.AFTER_12_WEEK_CORES,
            next_action_due_date=date(2021, 1, 1),
        ),
        MockCase(
            id=19,
            status=SimplifiedCase.Status.AFTER_12_WEEK_CORES,
            next_action_due_date=date(2021, 2, 1),
        ),
        MockCase(
            id=17,
            status=SimplifiedCase.Status.AFTER_12_WEEK_CORES,
        ),
    ],
    "in_correspondence_with_equalities_body": [
        MockCase(
            id=24,
            status=SimplifiedCase.Status.IN_CORES_WITH_ENFORCEMENT_BODY,
            report_followup_week_12_due_date=date(2021, 1, 1),
        ),
        MockCase(
            id=25,
            status=SimplifiedCase.Status.IN_CORES_WITH_ENFORCEMENT_BODY,
            report_followup_week_12_due_date=date(2021, 2, 1),
        ),
        MockCase(
            id=23,
            status=SimplifiedCase.Status.IN_CORES_WITH_ENFORCEMENT_BODY,
        ),
    ],
    "in_probation_period": [
        MockCase(
            id=15,
            status=SimplifiedCase.Status.AWAITING_12_WEEK_DEADLINE,
            next_action_due_date=date(2021, 1, 1),
        ),
        MockCase(
            id=16,
            status=SimplifiedCase.Status.AWAITING_12_WEEK_DEADLINE,
            next_action_due_date=date(2021, 2, 1),
        ),
        MockCase(
            id=14,
            status=SimplifiedCase.Status.AWAITING_12_WEEK_DEADLINE,
        ),
    ],
    "in_report_correspondence": [
        MockCase(
            id=12,
            status=SimplifiedCase.Status.IN_REPORT_CORES,
            next_action_due_date=date(2021, 1, 1),
        ),
        MockCase(
            id=13,
            status=SimplifiedCase.Status.IN_REPORT_CORES,
            next_action_due_date=date(2021, 2, 1),
        ),
        MockCase(id=11, status=SimplifiedCase.Status.IN_REPORT_CORES),
    ],
    "report_ready_to_send": [
        MockCase(
            id=9,
            status=SimplifiedCase.Status.REPORT_READY_TO_SEND,
        ),
        MockCase(
            id=10,
            status=SimplifiedCase.Status.REPORT_READY_TO_SEND,
        ),
    ],
    "reports_in_progress": [
        MockCase(
            id=7,
            status=SimplifiedCase.Status.REPORT_IN_PROGRESS,
        ),
        MockCase(
            id=8,
            status=SimplifiedCase.Status.REPORT_IN_PROGRESS,
        ),
    ],
    "qa_in_progress": [
        MockCase(
            id=26,
            status=SimplifiedCase.Status.QA_IN_PROGRESS,
        ),
        MockCase(
            id=27,
            status=SimplifiedCase.Status.QA_IN_PROGRESS,
        ),
        MockCase(
            id=30,
            status=SimplifiedCase.Status.QA_IN_PROGRESS,
        ),
    ],
    "test_in_progress": [
        MockCase(
            id=5,
            status=SimplifiedCase.Status.TEST_IN_PROGRESS,
        ),
        MockCase(
            id=6,
            status=SimplifiedCase.Status.TEST_IN_PROGRESS,
        ),
    ],
    "unknown": [],
    "unassigned_case": [
        MockCase(id=1),
        MockCase(id=2),
        MockCase(
            id=3,
            status=SimplifiedCase.Status.UNASSIGNED,
        ),
        MockCase(
            id=4,
            status=SimplifiedCase.Status.UNASSIGNED,
        ),
        MockCase(
            id=28,
            qa_status=SimplifiedCase.QAStatus.IN_QA,
        ),
        MockCase(
            id=29,
            qa_status=SimplifiedCase.QAStatus.IN_QA,
        ),
    ],
    "case_closed_waiting_to_be_sent": [
        MockCase(
            id=31,
            status=SimplifiedCase.Status.CASE_CLOSED_WAITING_TO_SEND,
            case_close_complete_date=FIRST_DATE,
        ),
    ],
    "case_closed_sent_to_equalities_body": [
        MockCase(
            id=32,
            status=SimplifiedCase.Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY,
            sent_to_enforcement_body_sent_date=FIRST_DATE,
        ),
    ],
    "reviewing_changes": [
        MockCase(
            id=33,
            status=SimplifiedCase.Status.REVIEWING_CHANGES,
            twelve_week_correspondence_acknowledged_date=FIRST_DATE,
        ),
    ],
    "completed": [],
}

EXPECTED_MOCK_CASES_IN_QA = [
    MockCase(
        id=26,
        status=SimplifiedCase.Status.QA_IN_PROGRESS,
    ),
    MockCase(
        id=27,
        status=SimplifiedCase.Status.QA_IN_PROGRESS,
    ),
    MockCase(
        id=30,
        status=SimplifiedCase.Status.QA_IN_PROGRESS,
    ),
]


@dataclass
class MockDetailedCase:
    """Mock of detailed case for testing"""

    id: int
    status: str = DetailedCase.Status.UNASSIGNED


MOCK_DETAILED_CASES: list[MockDetailedCase] = [
    MockDetailedCase(id=3),
    MockDetailedCase(id=2),
    MockDetailedCase(id=1, status=DetailedCase.Status.BLOCKED),
]


def test_group_cases_by_status():
    """Test cases are grouped by status and sorted"""
    assert group_cases_by_status(simplified_cases=MOCK_CASES) == EXPECTED_MOCK_CASES_BY_STATUS  # type: ignore


def test_group_detailed_cases_by_status():
    """Test detailed cases are grouped by status and sorted"""
    detailed_cases_by_status: dict = group_detailed_or_mobile_cases_by_status(
        cases=MOCK_DETAILED_CASES
    )

    assert len(detailed_cases_by_status) == len(DetailedCase.Status.choices)

    assert DetailedCase.Status.UNASSIGNED in detailed_cases_by_status

    unassigned_detailed_cases: dict = detailed_cases_by_status[
        DetailedCase.Status.UNASSIGNED
    ]

    assert unassigned_detailed_cases["cases"] == [
        MockDetailedCase(id=2),
        MockDetailedCase(id=3),
    ]

    assert DetailedCase.Status.BLOCKED in detailed_cases_by_status

    blocked_detailed_cases: dict = detailed_cases_by_status[DetailedCase.Status.BLOCKED]

    assert blocked_detailed_cases["cases"] == [
        MockDetailedCase(id=1, status=DetailedCase.Status.BLOCKED)
    ]


def test_get_all_cases_in_qa():
    """Test cases in qa are sorted and returned"""
    assert get_all_cases_in_qa(all_cases=MOCK_CASES) == EXPECTED_MOCK_CASES_IN_QA  # type: ignore


def test_return_cases_requiring_user_review():
    """Test cases in QA for a specific user are returned"""
    user: User = User()

    mock_case_1: MockCase = MockCase(
        id=1,
        reviewer=user,
        qa_status=SimplifiedCase.QAStatus.IN_QA,
    )
    mock_case_2: MockCase = MockCase(
        id=2,
        reviewer=user,
        qa_status=SimplifiedCase.QAStatus.IN_QA,
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
