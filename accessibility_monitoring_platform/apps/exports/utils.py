"""Export utilities"""

from datetime import date

from django.db.models.query import QuerySet

from ..simplified.models import SimplifiedCase


def get_exportable_cases(
    cutoff_date: date, enforcement_body: SimplifiedCase.EnforcementBody
) -> QuerySet[SimplifiedCase]:
    """Return list of Cases to export for enforcement body"""
    return (
        SimplifiedCase.objects.filter(
            status=SimplifiedCase.Status.CASE_CLOSED_WAITING_TO_SEND
        )
        .filter(enforcement_body=enforcement_body)
        .filter(compliance_email_sent_date__lte=cutoff_date)
        .exclude(case_completed=SimplifiedCase.CaseCompleted.COMPLETE_NO_SEND)
        .order_by("id")
    )
