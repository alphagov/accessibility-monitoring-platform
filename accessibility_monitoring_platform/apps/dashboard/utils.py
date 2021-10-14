"""
Utility functions used in dashboard
"""

from datetime import datetime, timedelta
from typing import Dict, List

from django.contrib.auth.models import User
from django.utils import timezone

from ..cases.models import Case, STATUS_READY_TO_QA


def group_cases_by_status(cases: List[Case]) -> Dict[str, List[Case]]:
    """Group cases by status values; Sort by a specific column"""
    cases_by_status: Dict[str, List[Case]] = {}
    for key, status, field_to_sort_by in [
        ("unknown", "unknown", "id"),
        ("unassigned_cases", "unassigned-case", "id"),
        ("test_in_progress", "test-in-progress", "id"),
        ("reports_in_progress", "report-in-progress", "id"),
        ("report_ready_to_send", "report-ready-to-send", "id"),
        ("qa_in_progress", "qa-in-progress", "id"),
        (
            "in_report_correspondence",
            "in-report-correspondence",
            "next_action_due_date",
        ),
        (
            "in_probation_period",
            "in-probation-period",
            "next_action_due_date",
        ),
        (
            "in_12_week_correspondence",
            "in-12-week-correspondence",
            "next_action_due_date",
        ),
        (
            "final_decision_due",
            "final-decision-due",
            "report_followup_week_12_due_date",
        ),
        (
            "in_correspondence_with_equalities_body",
            "in-correspondence-with-equalities-body",
            "report_followup_week_12_due_date",
        ),
    ]:
        cases_by_status[key] = sorted(
            [case for case in cases if case.status == status],
            key=lambda case: (
                getattr(case, field_to_sort_by) is None,
                getattr(case, field_to_sort_by),
            ),
        )
    return cases_by_status


def group_cases_by_qa_status(cases: List[Case]) -> Dict[str, List[Case]]:
    """Group cases by qa_status values; Sort by a specific column"""
    cases_by_status: Dict[str, List[Case]] = {}
    for key, qa_status, field_to_sort_by in [
        ("ready_for_qa", STATUS_READY_TO_QA, "id"),
    ]:
        cases_by_status[key] = sorted(
            [case for case in cases if case.qa_status == qa_status],
            key=lambda case: getattr(case, field_to_sort_by),
        )
    return cases_by_status


def return_cases_requiring_user_review(cases: List[Case], user: User) -> List[Case]:
    """Find all cases where the user is the reviewer and return those in QA"""
    return sorted(
        [case for case in cases if case.reviewer == user and case.qa_status == "in-qa"],
        key=lambda case: case.id,
    )


def return_recently_completed_cases(cases: List[Case]) -> List[Case]:
    """Find cases which are complete and were completed in the last 30 days"""
    thirty_days_ago: datetime = timezone.now() - timedelta(30)
    return sorted(
        [
            case
            for case in cases
            if case.status == "complete"
            and case.completed_date
            and case.completed_date >= thirty_days_ago
        ],
        key=lambda case: (
            case.completed_date is None,
            case.completed_date,
        ),
    )
