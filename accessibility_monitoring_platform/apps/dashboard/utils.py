"""
Utility functions used in dashboard
"""

from django.contrib.auth.models import User

from ..simplified.models import SimplifiedCase


def group_cases_by_status(
    simplified_cases: list[SimplifiedCase],
) -> dict[str, list[SimplifiedCase]]:
    """Group cases by status values; Sort by a specific column"""
    cases_by_status: dict[str, list[SimplifiedCase]] = {}

    status_parametres: list[tuple[str, str, str]] = (
        [  # final dict key, status, and sort
            (
                "unknown",
                SimplifiedCase.Status.UNKNOWN,
                "id",
            ),
            (
                "test_in_progress",
                SimplifiedCase.Status.TEST_IN_PROGRESS,
                "id",
            ),
            (
                "reports_in_progress",
                SimplifiedCase.Status.REPORT_IN_PROGRESS,
                "id",
            ),
            (
                "report_ready_to_send",
                SimplifiedCase.Status.REPORT_READY_TO_SEND,
                "id",
            ),
            (
                "qa_in_progress",
                SimplifiedCase.Status.QA_IN_PROGRESS,
                "id",
            ),
            (
                "in_report_correspondence",
                SimplifiedCase.Status.IN_REPORT_CORES,
                "next_action_due_date",
            ),
            (
                "in_probation_period",
                SimplifiedCase.Status.AWAITING_12_WEEK_DEADLINE,
                "next_action_due_date",
            ),
            (
                "in_12_week_correspondence",
                SimplifiedCase.Status.IN_12_WEEK_CORES,
                "next_action_due_date",
            ),
            (
                "reviewing_changes",
                SimplifiedCase.Status.REVIEWING_CHANGES,
                "twelve_week_correspondence_acknowledged_date",
            ),
            (
                "final_decision_due",
                SimplifiedCase.Status.FINAL_DECISION_DUE,
                "report_followup_week_12_due_date",
            ),
            (
                "case_closed_waiting_to_be_sent",
                SimplifiedCase.Status.CASE_CLOSED_WAITING_TO_SEND,
                "case_close_complete_date",
            ),
            (
                "case_closed_sent_to_equalities_body",
                SimplifiedCase.Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY,
                "sent_to_enforcement_body_sent_date",
            ),
            (
                "in_correspondence_with_equalities_body",
                SimplifiedCase.Status.IN_CORES_WITH_ENFORCEMENT_BODY,
                "report_followup_week_12_due_date",
            ),
            (
                "completed",
                SimplifiedCase.Status.COMPLETE,
                "completed_date",
            ),
        ]
    )

    for status_key, status, field_to_sort_by in status_parametres:
        cases_by_status[status_key] = sorted(
            [
                simplified_case
                for simplified_case in simplified_cases
                if simplified_case.status == status
            ],
            key=lambda simplified_case, sort_key=field_to_sort_by: (
                getattr(simplified_case, sort_key) is None,
                getattr(simplified_case, sort_key),
            ),
        )
    return cases_by_status


def get_all_cases_in_qa(all_cases: list[SimplifiedCase]) -> list[SimplifiedCase]:
    """Return all cases in QA"""
    cases_in_qa = sorted(
        [
            simplified_case
            for simplified_case in all_cases
            if simplified_case.status == SimplifiedCase.Status.QA_IN_PROGRESS
        ],
        key=lambda simplified_case, sort_key="id": getattr(simplified_case, sort_key),
    )
    return cases_in_qa


def return_cases_requiring_user_review(
    simplified_cases: list[SimplifiedCase], user: User
) -> list[SimplifiedCase]:
    """Find all cases where the user is the reviewer and return those in QA"""
    cases_requiring_user_review: list[SimplifiedCase] = [
        simplified_case
        for simplified_case in simplified_cases
        if simplified_case.reviewer == user and simplified_case.qa_status == "in-qa"
    ]
    return sorted(  # sort by case ID
        cases_requiring_user_review,
        key=lambda case: case.id,  # type: ignore
    )
