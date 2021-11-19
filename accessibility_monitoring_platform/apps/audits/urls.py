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
    AuditManualByPageUpdateView,
    AuditAxeUpdateView,
    CheckResultView,
    AuditPdfUpdateView,
    AuditStatement1UpdateView,
    AuditStatement2UpdateView,
    AuditSummaryUpdateView,
    delete_audit,
    restore_audit,
)

app_name: str = "audits"
urlpatterns: List[URLPattern] = [
    path("create/", login_required(AuditCreateView.as_view()), name="audit-create"),
    path(
        "<int:pk>/view/", login_required(AuditDetailView.as_view()), name="audit-detail"
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
        login_required(AuditManualByPageUpdateView.as_view()),
        name="edit-audit-manual-by-page",
    ),
    path(
        "<int:audit_id>/pages/<int:page_id>/edit-audit-axe/",
        login_required(AuditAxeUpdateView.as_view()),
        name="edit-audit-axe",
    ),
    path(
        "<int:audit_id>/pages/<int:page_id>/wcag/<int:wcag_id>/edit-check-result/",
        login_required(CheckResultView.as_view()),
        name="edit-check-result",
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
]
