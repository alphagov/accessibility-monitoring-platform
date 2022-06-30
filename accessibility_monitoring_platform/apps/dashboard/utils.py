"""
Utility functions used in dashboard
"""

from typing import Dict, List
from django.contrib.auth.models import User
from ..cases.models import Case, STATUS_READY_TO_QA


def group_cases_by_status(cases: List[Case]) -> Dict[str, List[Case]]:
    """Group cases by status values; Sort by a specific column"""
    cases_by_status: Dict[str, List[Case]] = {}

    status_parametres: List[
        tuple[str, str, str]
    ] = [  # final dict key, status, and sort
        (
            "unknown",
            "unknown",
            "id",
        ),
        (
            "test_in_progress",
            "test-in-progress",
            "id",
        ),
        (
            "reports_in_progress",
            "report-in-progress",
            "id",
        ),
        (
            "report_ready_to_send",
            "report-ready-to-send",
            "id",
        ),
        (
            "qa_in_progress",
            "qa-in-progress",
            "id",
        ),
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
            "reviewing_changes",
            "reviewing-changes",
            "twelve_week_correspondence_acknowledged_date",
        ),
        (
            "final_decision_due",
            "final-decision-due",
            "report_followup_week_12_due_date",
        ),
        (
            "case_closed_waiting_to_be_sent",
            "case-closed-waiting-to-be-sent",
            "case_close_complete_date",
        ),
        (
            "case_closed_sent_to_equalities_body",
            "case-closed-sent-to-equalities-body",
            "sent_to_enforcement_body_sent_date",
        ),
        (
            "in_correspondence_with_equalities_body",
            "in-correspondence-with-equalities-body",
            "report_followup_week_12_due_date",
        ),
        (
            "completed",
            "complete",
            "completed_date",
        ),
    ]

    for status_key, status, field_to_sort_by in status_parametres:
        cases_by_status[status_key] = sorted(
            [case for case in cases if case.status == status],
            key=lambda case, sort_key=field_to_sort_by: (
                getattr(case, sort_key) is None,
                getattr(case, sort_key),
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
            key=lambda case, sort_key=field_to_sort_by: getattr(case, sort_key),
        )
    return cases_by_status


def return_cases_requiring_user_review(cases: List[Case], user: User) -> List[Case]:
    """Find all cases where the user is the reviewer and return those in QA"""
    cases_requiring_user_review: List[Case] = [
        case for case in cases if case.reviewer == user and case.qa_status == "in-qa"
    ]
    return sorted(  # sort by case ID
        cases_requiring_user_review,
        key=lambda case: case.id,  # type: ignore
    )
