"""
Utility functions used in dashboard
"""

from django.contrib.auth.models import User

from ..cases.models import Case, CaseStatus


def group_cases_by_status(cases: list[Case]) -> dict[str, list[Case]]:
    """Group cases by status values; Sort by a specific column"""
    cases_by_status: dict[str, list[Case]] = {}

    status_parametres: list[tuple[str, str, str]] = (
        [  # final dict key, status, and sort
            (
                "unknown",
                CaseStatus.Status.UNKNOWN,
                "id",
            ),
            (
                "test_in_progress",
                CaseStatus.Status.TEST_IN_PROGRESS,
                "id",
            ),
            (
                "reports_in_progress",
                CaseStatus.Status.REPORT_IN_PROGRESS,
                "id",
            ),
            (
                "report_ready_to_send",
                CaseStatus.Status.REPORT_READY_TO_SEND,
                "id",
            ),
            (
                "qa_in_progress",
                CaseStatus.Status.QA_IN_PROGRESS,
                "id",
            ),
            (
                "in_report_correspondence",
                CaseStatus.Status.IN_REPORT_CORES,
                "next_action_due_date",
            ),
            (
                "in_probation_period",
                CaseStatus.Status.AWAITING_12_WEEK_DEADLINE,
                "next_action_due_date",
            ),
            (
                "in_12_week_correspondence",
                CaseStatus.Status.IN_12_WEEK_CORES,
                "next_action_due_date",
            ),
            (
                "reviewing_changes",
                CaseStatus.Status.REVIEWING_CHANGES,
                "twelve_week_correspondence_acknowledged_date",
            ),
            (
                "final_decision_due",
                CaseStatus.Status.FINAL_DECISION_DUE,
                "report_followup_week_12_due_date",
            ),
            (
                "case_closed_waiting_to_be_sent",
                CaseStatus.Status.CASE_CLOSED_WAITING_TO_SEND,
                "case_close_complete_date",
            ),
            (
                "case_closed_sent_to_equalities_body",
                CaseStatus.Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY,
                "sent_to_enforcement_body_sent_date",
            ),
            (
                "in_correspondence_with_equalities_body",
                CaseStatus.Status.IN_CORES_WITH_ENFORCEMENT_BODY,
                "report_followup_week_12_due_date",
            ),
            (
                "completed",
                CaseStatus.Status.COMPLETE,
                "completed_date",
            ),
        ]
    )

    for status_key, status, field_to_sort_by in status_parametres:
        cases_by_status[status_key] = sorted(
            [case for case in cases if case.casestatus.status == status],
            key=lambda case, sort_key=field_to_sort_by: (
                getattr(case, sort_key) is None,
                getattr(case, sort_key),
            ),
        )
    return cases_by_status


def get_all_cases_in_qa(all_cases: list[Case]) -> list[Case]:
    """Return all cases in QA"""
    cases_in_qa = sorted(
        [
            case
            for case in all_cases
            if case.casestatus.status == CaseStatus.Status.QA_IN_PROGRESS
        ],
        key=lambda case, sort_key="id": getattr(case, sort_key),
    )
    return cases_in_qa


def return_cases_requiring_user_review(cases: list[Case], user: User) -> list[Case]:
    """Find all cases where the user is the reviewer and return those in QA"""
    cases_requiring_user_review: list[Case] = [
        case for case in cases if case.reviewer == user and case.qa_status == "in-qa"
    ]
    return sorted(  # sort by case ID
        cases_requiring_user_review,
        key=lambda case: case.id,  # type: ignore
    )
