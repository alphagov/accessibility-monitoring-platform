"""Export utilities"""

from datetime import date

from ..cases.models import Case, CaseStatus


def get_exportable_cases(
    cutoff_date: date, enforcement_body: Case.EnforcementBody
) -> list[Case]:
    """Return list of Cases to export for enforcement body"""
    return [
        case_status.case
        for case_status in CaseStatus.objects.filter(
            status=CaseStatus.Status.CASE_CLOSED_WAITING_TO_SEND
        )
        .filter(case__enforcement_body=enforcement_body)
        .filter(case__compliance_email_sent_date__lte=cutoff_date)
        .exclude(case__case_completed=Case.CaseCompleted.COMPLETE_NO_SEND)
        .order_by("case__id")
    ]
