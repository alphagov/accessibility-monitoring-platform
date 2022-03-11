"""
Views for audits app (called tests by users)
"""
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse

from .models import Report

from ..cases.models import Case

from ..common.utils import (
    record_model_create_event,
)


def create_report(request: HttpRequest, case_id: int) -> HttpResponse:
    """
    Create report

    Args:
        request (HttpRequest): Django HttpRequest
        case_id (int): Id of parent case

    Returns:
        HttpResponse: Django HttpResponse
    """
    case: Case = get_object_or_404(Case, id=case_id)
    report: Report = Report.objects.create(case=case)
    record_model_create_event(user=request.user, model_object=report)  # type: ignore
    return redirect(reverse("reports:edit-report-metadata", kwargs={"pk": report.id}))  # type: ignore
