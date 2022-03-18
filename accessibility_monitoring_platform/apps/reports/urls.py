"""
URLS for dashboard
"""
from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern
from .views import (
    create_report,
    rebuild_report,
    ReportDetailView,
    ReportMetadataUpdateView,
    SectionUpdateView,
    ReportPreviewTemplateView,
    publish_report,
    PublishedReportListView,
    PublishedReportDetailView,
)

app_name: str = "reports"
urlpatterns: List[URLPattern] = [
    path(
        "create-for-case/<int:case_id>/",
        login_required(create_report),
        name="report-create",
    ),
    path(
        "<int:pk>/report-rebuild/",
        login_required(rebuild_report),
        name="report-rebuild",
    ),
    path(
        "<int:pk>/report-preview/",
        login_required(ReportPreviewTemplateView.as_view()),
        name="report-preview",
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
        "<int:pk>/edit-section/",
        login_required(SectionUpdateView.as_view()),
        name="edit-report-section",
    ),
    path(
        "<int:pk>/report-publish/",
        login_required(publish_report),
        name="report-publish",
    ),
    path(
        "<int:pk>/published-reports/",
        login_required(PublishedReportListView.as_view()),
        name="published-report-list",
    ),
    path(
        "<int:pk>/published_report/",
        login_required(PublishedReportDetailView.as_view()),
        name="published-report-detail",
    ),
]
