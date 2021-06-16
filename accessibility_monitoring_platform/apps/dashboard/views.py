"""
Views for dashboard.

Home should be the only view for dashboard.
"""
from datetime import date
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


def sort_cases(query_set, status=None):
    if status == "new_case":
        return query_set.filter(
            Q(auditor__isnull=True) | Q(contact__case__isnull=True),
            report_sent_date__isnull=True,
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        )

    if status == "test_in_progress":
        return query_set.filter(
            Q(test_status="in-progress") | Q(test_status="not-started"),
            auditor__isnull=False,
            contact__case__isnull=False,
            report_sent_date__isnull=True,
            report_acknowledged_date__isnull=True,
            week_12_followup_date__isnull=True,
            compliance_email_sent_date__isnull=True,
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        )

    if status == "report_in_progress":
        return query_set.filter(
            test_status="complete",
            report_sent_date__isnull=True,
            report_acknowledged_date__isnull=True,
            week_12_followup_date__isnull=True,
            compliance_email_sent_date__isnull=True,
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        )

    if status == "awaiting_response_to_report":
        return query_set.filter(
            report_sent_date__isnull=False,
            report_acknowledged_date__isnull=True,
            week_12_followup_date__isnull=True,
            compliance_email_sent_date__isnull=True,
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        ).order_by("report_sent_date")

    if status == "twelve_week_review_due":
        return query_set.filter(
            report_acknowledged_date__isnull=False,
            compliance_email_sent_date__isnull=True,
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        ).order_by("week_12_followup_date")

    if status == "update_for_enforcement_bodies_due":
        return query_set.filter(
            compliance_email_sent_date__isnull=False,
            is_case_completed=False,
            is_archived=False,
            is_public_sector_body=True
        )

    if status == "recently_completed":
        date = datetime.datetime.now() - datetime.timedelta(30)
        return query_set.filter(
            is_case_completed=True,
            completed__gte=date,
            is_archived=False,
            is_public_sector_body=True
        )

    if status == "qa_cases":
        return query_set.filter(
            report_review_status="ready-to-review",
            report_approved_status="no",
            is_archived=False,
            is_public_sector_body=True
        )

    return None


# @property
# def is_past_due(self):
#     return date.today() > self.date


@login_required
def home(request: HttpRequest) -> HttpResponse:
    """
    View for the main dashboard

    Args:
        request (HttpRequest): Django request

    Returns:
        HttpResponse: Django http response
    """
    request_temp: Any = request
    user: User = get_object_or_404(User, id=request_temp.user.id)
    all_entries = Case.objects.all()
    user_entries = Case.objects.filter(auditor=user).order_by("created")
    qa_entries = Case.objects.filter(reviewer=user).order_by("created")
    sorted_cases = {
        "new_case": sort_cases(user_entries, "new_case"),
        "test_in_progress": sort_cases(user_entries, "test_in_progress"),
        "reports_in_progress": sort_cases(user_entries, "report_in_progress"),
        "qa_cases": sort_cases(qa_entries, "qa_cases"),
        "awaiting_response_to_report": sort_cases(user_entries, "awaiting_response_to_report"),
        "twelve_week_review_due": sort_cases(user_entries, "twelve_week_review_due"),
        "update_for_enforcement_bodies_due": sort_cases(user_entries, "update_for_enforcement_bodies_due"),
        "recently_completed": sort_cases(user_entries, "recently_completed"),
    }

    headers = {
        "new_case": ["Date created", "Case", "Organisation", "Step progress"],
        "test_in_progress": ["Date created", "Case", "Organisation", "Step progress"],
        "reports_in_progress": ["Date created", "Case", "Organisation", "Step progress"],
        "qa_cases": ["Date created", "Case", "Organisation", "Step progress"],
        "awaiting_response_to_report": ["Days since being sent", "Case", "Organisation", "Step progress"],
        "twelve_week_review_due": ["Review due", "Case", "Organisation", "Step progress"],
        "update_for_enforcement_bodies_due": ["Review due", "Case", "Organisation", "Step progress"],
        "recently_completed": ["Completed on", "Case", "Organisation", "Step progress"]
    }

    context = {
        "sorted_cases": sorted_cases,
        "headers": headers,
        "total_cases": len(all_entries),
        "your_cases": len(user_entries),
        "unassigned_cases": len(all_entries.filter(
            auditor__isnull=True,
            is_archived=False,
            is_public_sector_body=True
        )),
        "unassigned_qa_cases": len(all_entries.filter(
            reviewer__isnull=True,
            report_review_status="ready-to-review",
            report_approved_status="no",
            is_archived=False,
            is_public_sector_body=True
        )),
        "today": date.today()
    }
    return render(request, "dashboard/home.html", context)
