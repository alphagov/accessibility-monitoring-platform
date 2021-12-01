"""
URLS for dashboard
"""
from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern
from .views import (
    AuditCreateView,
    AuditDetailView,
    AuditMetadataUpdateView,
    AuditPagesUpdateView,
    AuditManualFormView,
    AuditAxeFormView,
    AuditPdfUpdateView,
    AuditStatement1UpdateView,
    AuditStatement2UpdateView,
    AuditSummaryUpdateView,
    AuditReportOptionsUpdateView,
    AuditReportTextUpdateView,
    delete_audit,
    restore_audit,
)

app_name: str = "audits"
urlpatterns: List[URLPattern] = [
    path(
        "create-for-case/<int:case_id>/",
        login_required(AuditCreateView.as_view()),
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
        "<int:audit_id>/pages/<int:page_id>/edit-audit-manual/",
        login_required(AuditManualFormView.as_view()),
        name="edit-audit-manual",
    ),
    path(
        "<int:audit_id>/pages/<int:page_id>/edit-audit-axe/",
        login_required(AuditAxeFormView.as_view()),
        name="edit-audit-axe",
    ),
    path(
        "<int:pk>/edit-audit-pdf/",
        login_required(AuditPdfUpdateView.as_view()),
        name="edit-audit-pdf",
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
