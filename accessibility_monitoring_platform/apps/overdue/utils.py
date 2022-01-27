from typing import Union
from datetime import datetime, timedelta
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from ..cases.models import Case


def get_overdue_cases(user_request: User) -> Union[QuerySet[Case], None]:
    """ Filters cases with overdue correspondence actions"""
    if user_request.id:  # type: ignore
        user: User = get_object_or_404(User, id=user_request.id)  # type: ignore
        user_cases: QuerySet[Case] = Case.objects.filter(auditor=user)
        start_date: datetime = datetime(2020, 1, 1)
        end_date: datetime = datetime.now() - timedelta(days=1)

        in_report_correspondence: QuerySet[Case] = user_cases.filter(
            Q(status="in-report-correspondence"),
            Q(
                Q(
                    report_followup_week_1_due_date__range=[start_date, end_date],
                    report_followup_week_1_sent_date=None
                )
                | Q(
                    report_followup_week_4_due_date__range=[start_date, end_date],
                    report_followup_week_4_sent_date=None
                )
                | Q(
                    report_followup_week_4_sent_date__range=[start_date, end_date]
                )
            )
        )

        in_probation_period: QuerySet[Case] = user_cases.filter(
            status__icontains="in-probation-period",
            report_followup_week_12_due_date__range=[start_date, end_date]
        )

        in_12_week_correspondence: QuerySet[Case] = user_cases.filter(
            Q(status__icontains="in-12-week-correspondence"),
            Q(
                Q(
                    twelve_week_1_week_chaser_due_date__range=[start_date, end_date],
                    twelve_week_1_week_chaser_sent_date=None
                )
                | Q(
                    twelve_week_4_week_chaser_due_date__range=[start_date, end_date],
                    twelve_week_4_week_chaser_sent_date=None
                )
                | Q(
                    twelve_week_4_week_chaser_sent_date__range=[start_date, end_date]
                )
            )
        )

        in_correspondence: QuerySet[Case] = in_report_correspondence | in_probation_period | in_12_week_correspondence

        in_correspondence: QuerySet[Case] = sorted(in_correspondence, key=lambda t: t.next_action_due_date)  # type: ignore
        return in_correspondence


def get_number_of_overdue_cases(user_request: User) -> int:
    res: Union[QuerySet[Case], None] = get_overdue_cases(user_request)
    if res:
        return len(res)
    return 0
