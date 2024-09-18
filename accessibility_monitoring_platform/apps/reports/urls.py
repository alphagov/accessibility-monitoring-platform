"""
URLS for dashboard
"""

from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from .views import (
    ReportNotesUpdateView,
    ReportPreviewTemplateView,
    ReportRepublishTemplateView,
    ReportVisitsMetricsView,
    ReportWrapperUpdateView,
    create_report,
    publish_report,
)

app_name: str = "reports"
urlpatterns: List[URLPattern] = [
    path(
        "create-for-case/<int:case_id>/",
        login_required(create_report),
        name="report-create",
    ),
    path(
        "<int:pk>/report-preview/",
        login_required(ReportPreviewTemplateView.as_view()),
        name="report-preview",
    ),
    path(
        "<int:pk>/edit-report-notes/",
        login_required(ReportNotesUpdateView.as_view()),
        name="edit-report-notes",
    ),
    path(
        "<int:pk>/report-republish/",
        login_required(ReportRepublishTemplateView.as_view()),
        name="report-republish",
    ),
    path(
        "<int:pk>/publish-report/",
        login_required(publish_report),
        name="publish-report",
    ),
    path(
        "edit-report-wrapper/",
        login_required(ReportWrapperUpdateView.as_view()),
        name="edit-report-wrapper",
    ),
    path(
        "<int:pk>/report-metrics-view/",
        login_required(ReportVisitsMetricsView.as_view()),
        name="report-metrics-view",
    ),
]
