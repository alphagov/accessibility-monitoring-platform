"""
URLS for dashboard
"""
from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern
from .views import (
    AuditAllIssuesListView,
    AuditDetailView,
    AuditMetadataUpdateView,
    AuditPagesUpdateView,
    AuditPageChecksFormView,
    AuditStatement1UpdateView,
    AuditStatement2UpdateView,
    AuditSummaryUpdateView,
    AuditReportOptionsUpdateView,
    AuditReportTextUpdateView,
    create_audit,
    delete_audit,
    restore_audit,
    delete_page,
    restore_page,
)

app_name: str = "audits"
urlpatterns: List[URLPattern] = [
    path(
        "all-issues/",
        login_required(AuditAllIssuesListView.as_view()),
        name="audit-all-issues",
    ),
    path(
        "create-for-case/<int:case_id>/",
        login_required(create_audit),
        name="audit-create",
    ),
    path(
        "<int:pk>/detail/",
        login_required(AuditDetailView.as_view()),
        name="audit-detail",
    ),
    path(
        "<int:pk>/delete-audit/",
        login_required(delete_audit),
        name="delete-audit",
    ),
    path(
        "<int:pk>/restore-audit/",
        login_required(restore_audit),
        name="restore-audit",
    ),
    path(
        "<int:pk>/edit-audit-metadata/",
        login_required(AuditMetadataUpdateView.as_view()),
        name="edit-audit-metadata",
    ),
    path(
        "<int:pk>/edit-audit-pages/",
        login_required(AuditPagesUpdateView.as_view()),
        name="edit-audit-pages",
    ),
    path(
        "pages/<int:pk>/delete-page/",
        login_required(delete_page),
        name="delete-page",
    ),
    path(
        "pages/<int:pk>/restore-page/",
        login_required(restore_page),
        name="restore-page",
    ),
    path(
        "pages/<int:pk>/edit-audit-page-checks/",
        login_required(AuditPageChecksFormView.as_view()),
        name="edit-audit-page-checks",
    ),
    path(
        "<int:pk>/edit-audit-statement-one/",
        login_required(AuditStatement1UpdateView.as_view()),
        name="edit-audit-statement-1",
    ),
    path(
        "<int:pk>/edit-audit-statement-two/",
        login_required(AuditStatement2UpdateView.as_view()),
        name="edit-audit-statement-2",
    ),
    path(
        "<int:pk>/edit-audit-summary/",
        login_required(AuditSummaryUpdateView.as_view()),
        name="edit-audit-summary",
    ),
    path(
        "<int:pk>/edit-audit-report-options/",
        login_required(AuditReportOptionsUpdateView.as_view()),
        name="edit-audit-report-options",
    ),
    path(
        "<int:pk>/edit-audit-report-text/",
        login_required(AuditReportTextUpdateView.as_view()),
        name="edit-audit-report-text",
    ),
]
