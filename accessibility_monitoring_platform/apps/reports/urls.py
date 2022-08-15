"""
URLS for dashboard
"""
from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern
from .views import (
    create_report,
    ReportConfirmRefreshTemplateView,
    rebuild_report,
    ReportDetailView,
    ReportMetadataUpdateView,
    SectionUpdateView,
    ReportPublisherTemplateView,
    ReportConfirmPublishTemplateView,
    publish_report,
    ReportWrapperUpdateView,
    ReportVisitsMetricsView,
)

app_name: str = "reports"
urlpatterns: List[URLPattern] = [
    path(
        "create-for-case/<int:case_id>/",
        login_required(create_report),
        name="report-create",
    ),
    path(
        "<int:pk>/report-confirm-refresh/",
        login_required(ReportConfirmRefreshTemplateView.as_view()),
        name="report-confirm-refresh",
    ),
    path(
        "<int:pk>/report-rebuild/",
        login_required(rebuild_report),
        name="report-rebuild",
    ),
    path(
        "<int:pk>/report-publisher/",
        login_required(ReportPublisherTemplateView.as_view()),
        name="report-publisher",
    ),
    path(
        "<int:pk>/detail/",
        login_required(ReportDetailView.as_view()),
        name="report-detail",
    ),
    path(
        "<int:pk>/edit-report-metadata/",
        login_required(ReportMetadataUpdateView.as_view()),
        name="edit-report-metadata",
    ),
    path(
        "sections/<int:pk>/edit-section/",
        login_required(SectionUpdateView.as_view()),
        name="edit-report-section",
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
