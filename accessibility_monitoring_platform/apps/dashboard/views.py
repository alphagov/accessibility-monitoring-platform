"""
Views for dashboard.

Home should be the only view for dashboard.
"""

from django.shortcuts import render
from ..cases.models import Case
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import (
    HttpRequest,
    HttpResponse
)
from typing import Any
import datetime
from django.db.models import Q


def sort_cases(query_set):
    new_case = query_set.filter(
        Q(auditor__isnull=True) | Q(contact__case__isnull=True),
        report_sent_date__isnull=True,
        is_case_completed=False,
        archived=False,
        is_public_sector_body=True
    )

    test_in_progress = query_set.filter(
        Q(test_status="in-progress") | Q(test_status="not-started"),
        auditor__isnull=False,
        contact__case__isnull=False,
        report_sent_date__isnull=True,
        report_acknowledged_date__isnull=True,
        week_12_followup_date__isnull=True,
        compliance_email_sent_date__isnull=True,
        is_case_completed=False,
        archived=False,
        is_public_sector_body=True
    )

    report_in_progress = query_set.filter(
        test_status="complete",
        report_sent_date__isnull=True,
        report_acknowledged_date__isnull=True,
        week_12_followup_date__isnull=True,
        compliance_email_sent_date__isnull=True,
        is_case_completed=False,
        archived=False,
        is_public_sector_body=True
    )

    awaiting_response_to_report = query_set.filter(
        report_sent_date__isnull=False,
        report_acknowledged_date__isnull=True,
        week_12_followup_date__isnull=True,
        compliance_email_sent_date__isnull=True,
        is_case_completed=False,
        archived=False,
        is_public_sector_body=True
    )

    twelve_weeks_review_due = query_set.filter(
        week_12_followup_date__lte=datetime.datetime.now(),
        compliance_email_sent_date__isnull=True,
        is_case_completed=False,
        archived=False,
        is_public_sector_body=True
    )

    update_for_enforcement_bodies_due = query_set.filter(
        compliance_email_sent_date__isnull=False,
        is_case_completed=False,
        archived=False,
        is_public_sector_body=True
    )

    date = datetime.datetime.now() - datetime.timedelta(30)

    recently_completed = query_set.filter(
        is_case_completed=True,
        completed__gte=date,
        archived=False,
        is_public_sector_body=True
    )

    # print(">>> New case")
    # print(len(new_case))
    # print(">>>")

    # print(">>> test_in_progress")
    # print(len(test_in_progress))
    # print(">>>")

    # print(">>> report_in_progress")
    # print(len(report_in_progress))
    # print(">>>")

    # print(">>> awaiting_response_to_report")
    # print(len(awaiting_response_to_report))
    # print(">>>")

    # print(">>> twelve_weeks_review_due")
    # print(len(twelve_weeks_review_due))
    # print(">>>")

    # print(">>> update_for_enforcement_bodies_due")
    # print(len(update_for_enforcement_bodies_due))
    # print(">>>")

    # print(">>> recently_completed")
    # print(len(recently_completed))
    # print(">>>")
    return {
        "new_case": new_case,
        "test_in_progress": test_in_progress,
        "report_in_progress": report_in_progress,
        "awaiting_response_to_report": awaiting_response_to_report,
        "twelve_weeks_review_due": twelve_weeks_review_due,
        "update_for_enforcement_bodies_due": update_for_enforcement_bodies_due,
        "recently_completed": recently_completed
    }



@login_required
def home(request: HttpRequest) -> HttpResponse:
    """
    View for the main dashboard

    Args:
        request (HttpRequest): Django request

    Returns:
        HttpResponse: Django http response
    """
    # request_temp: Any = request
    # user: User = get_object_or_404(User, id=request_temp.user.id)
    # c = Case.objects.get(auditor="Firstname Lastname")
    all_entries = Case.objects.all()
    sort_cases(all_entries)
    return render(request, "dashboard/home.html")
