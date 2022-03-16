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
        "<int:pk>/detail/",
        login_required(ReportDetailView.as_view()),
        name="report-detail",
    ),
    path(
        "<int:pk>/edit-report-metadata/",
        login_required(ReportMetadataUpdateView.as_view()),
        name="edit-report-metadata",
    ),
]
