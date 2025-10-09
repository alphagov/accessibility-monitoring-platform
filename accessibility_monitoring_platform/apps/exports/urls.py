"""
URLS for comments
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from .views import (
    ConfirmExportUpdateView,
    ExportCaseAsEmailDetailView,
    ExportConfirmDeleteUpdateView,
    ExportCreateView,
    ExportDetailView,
    ExportListView,
    ExportPreviewDetailView,
    export_all_cases,
    export_ready_cases,
    mark_all_export_cases_as_ready,
    mark_export_case_as_excluded,
    mark_export_case_as_ready,
    mark_export_case_as_unready,
)

app_name: str = "exports"
urlpatterns: list[URLPattern] = [
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
        "<int:pk>/export-preview/",
        login_required(ExportPreviewDetailView.as_view()),
        name="export-preview",
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
        login_required(ConfirmExportUpdateView.as_view()),
        name="export-confirm-export",
    ),
    path(
        "<int:pk>/mark-all-cases-as-ready/",
        login_required(mark_all_export_cases_as_ready),
        name="mark-all-cases-as-ready",
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
        login_required(export_ready_cases),
        name="export-ready-cases",
    ),
    path(
        "<int:export_id>/cases/<int:pk>/export-as-email/",
        login_required(ExportCaseAsEmailDetailView.as_view()),
        name="export-case-as-email",
    ),
]
