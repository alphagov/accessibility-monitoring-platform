"""
URLS for comments
"""

from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from .views import (
    ConfirmExportDetailView,
    ExportConfirmDeleteUpdateView,
    ExportCreateView,
    ExportDetailView,
    ExportListView,
    export_all_cases,
    export_and_bulk_update_ready_cases,
    mark_export_case_as_excluded,
    mark_export_case_as_ready,
    mark_export_case_as_unready,
)

app_name: str = "exports"
urlpatterns: List[URLPattern] = [
    path(
        "export-list/",
        login_required(ExportListView.as_view()),
        name="export-list",
    ),
    path(
        "export-create/",
        login_required(ExportCreateView.as_view()),
        name="export-create",
    ),
    path(
        "<int:pk>/export-detail/",
        login_required(ExportDetailView.as_view()),
        name="export-detail",
    ),
    path(
        "<int:pk>/export-all-cases/",
        login_required(export_all_cases),
        name="export-all-cases",
    ),
    path(
        "<int:pk>/export-confirm-delete/",
        login_required(ExportConfirmDeleteUpdateView.as_view()),
        name="export-confirm-delete",
    ),
    path(
        "<int:pk>/export-confirm-export/",
        login_required(ConfirmExportDetailView.as_view()),
        name="export-confirm-export",
    ),
    path(
        "<int:pk>/case-mark-as-ready/",
        login_required(mark_export_case_as_ready),
        name="case-mark-as-ready",
    ),
    path(
        "<int:pk>/case-mark-as-excluded/",
        login_required(mark_export_case_as_excluded),
        name="case-mark-as-excluded",
    ),
    path(
        "<int:pk>/case-mark-as-unready/",
        login_required(mark_export_case_as_unready),
        name="case-mark-as-unready",
    ),
    path(
        "<int:pk>/export-ready-cases/",
        login_required(export_and_bulk_update_ready_cases),
        name="export-ready-cases",
    ),
]
