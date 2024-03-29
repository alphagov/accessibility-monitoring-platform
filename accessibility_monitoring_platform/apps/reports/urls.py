"""
URLS for dashboard
"""
from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from .views import (
    ReportConfirmPublishTemplateView,
    ReportNotesUpdateView,
    ReportPublisherTemplateView,
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
        "<int:pk>/report-publisher/",
        login_required(ReportPublisherTemplateView.as_view()),
        name="report-publisher",
    ),
    path(
        "<int:pk>/edit-report-notes/",
        login_required(ReportNotesUpdateView.as_view()),
        name="edit-report-notes",
    ),
    path(
        "<int:pk>/report-confirm-publish/",
        login_required(ReportConfirmPublishTemplateView.as_view()),
        name="report-confirm-publish",
    ),
    path(
        "<int:pk>/report-publish/",
        login_required(publish_report),
        name="report-publish",
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
