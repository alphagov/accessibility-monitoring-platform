"""
URLS for dashboard
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from accessibility_monitoring_platform.apps.cases.views import (
    archive_case,
    export_cases,
    CaseCreateView,
    CaseContactFormsetUpdateView,
    CaseDetailView,
    CaseListView,
    CaseWebsiteDetailUpdateView,
    CaseTestResultsUpdateView,
    CaseReportDetailsUpdateView,
    CasePostReportDetailsUpdateView,
)

app_name = "cases"
urlpatterns = [
    path("", login_required(CaseListView.as_view()), name="case-list"),
    path("export", login_required(export_cases), name="case-export-cases"),
    path("create", login_required(CaseCreateView.as_view()), name="case-create"),
    path("<int:pk>/view", login_required(CaseDetailView.as_view()), name="case-detail"),
    path(
        "<int:pk>/edit-website-details",
        login_required(CaseWebsiteDetailUpdateView.as_view()),
        name="edit-website-details",
    ),
    path(
        "<int:pk>/edit-contact-details",
        login_required(CaseContactFormsetUpdateView.as_view()),
        name="edit-contact-details",
    ),
    path(
        "<int:pk>/edit-test-results",
        login_required(CaseTestResultsUpdateView.as_view()),
        name="edit-test-results",
    ),
    path(
        "<int:pk>/edit-report-details",
        login_required(CaseReportDetailsUpdateView.as_view()),
        name="edit-report-details",
    ),
    path(
        "<int:pk>/edit-post-report-details",
        login_required(CasePostReportDetailsUpdateView.as_view()),
        name="edit-post-report-details",
    ),
    path("<int:pk>/archive-case", login_required(archive_case), name="archive-case"),
]
