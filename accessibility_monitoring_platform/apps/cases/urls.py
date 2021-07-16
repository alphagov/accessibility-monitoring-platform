"""
URLS for dashboard
"""
from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern
from accessibility_monitoring_platform.apps.cases.views import (
    export_cases,
    export_single_case,
    CaseCreateView,
    CaseContactFormsetUpdateView,
    CaseDetailView,
    CaseListView,
    CaseDetailUpdateView,
    CaseTestResultsUpdateView,
    CaseReportDetailsUpdateView,
    CasePostReportDetailsUpdateView,
    CaseReportFollowupDueDatesUpdateView,
    CaseArchiveUpdateView,
    CaseNoPSBContactUpdateView,
)

app_name: str = "cases"
urlpatterns: List[URLPattern] = [
    path("", login_required(CaseListView.as_view()), name="case-list"),
    path("export-as-csv/", login_required(export_cases), name="case-export-list"),
    path(
        "<int:pk>/export-as-csv/",
        login_required(export_single_case),
        name="case-export-single",
    ),
    path("create/", login_required(CaseCreateView.as_view()), name="case-create"),
    path(
        "<int:pk>/view/", login_required(CaseDetailView.as_view()), name="case-detail"
    ),
    path(
        "<int:pk>/edit-case-details/",
        login_required(CaseDetailUpdateView.as_view()),
        name="edit-case-details",
    ),
    path(
        "<int:pk>/edit-contact-details/",
        login_required(CaseContactFormsetUpdateView.as_view()),
        name="edit-contact-details",
    ),
    path(
        "<int:pk>/edit-test-results/",
        login_required(CaseTestResultsUpdateView.as_view()),
        name="edit-test-results",
    ),
    path(
        "<int:pk>/edit-report-details/",
        login_required(CaseReportDetailsUpdateView.as_view()),
        name="edit-report-details",
    ),
    path(
        "<int:pk>/edit-no-psb-contact/",
        login_required(CaseNoPSBContactUpdateView.as_view()),
        name="edit-no-psb-contact",
    ),
    path(
        "<int:pk>/edit-post-report-details/",
        login_required(CasePostReportDetailsUpdateView.as_view()),
        name="edit-post-report-details",
    ),
    path(
        "<int:pk>/edit-report-followup-due-dates/",
        login_required(CaseReportFollowupDueDatesUpdateView.as_view()),
        name="edit-report-followup-due-dates",
    ),
    path(
        "<int:pk>/archive-case/",
        login_required(CaseArchiveUpdateView.as_view()),
        name="archive-case",
    ),
]
