"""
URLS for common
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from .views import (
    AccessibilityStatementTemplateView,
    ActiveQAAuditorUpdateView,
    BulkURLSearchView,
    ChangeToPlatformListView,
    ContactAdminView,
    EmailTemplateCreateView,
    EmailTemplateListView,
    EmailTemplatePreviewDetailView,
    EmailTemplateUpdateView,
    FooterLinkFormsetTemplateView,
    FrequentlyUsedLinkFormsetTemplateView,
    IssueReportListView,
    IssueReportView,
    MarkdownCheatsheetTemplateView,
    MetricsCaseTemplateView,
    MetricsPolicyTemplateView,
    MetricsReportTemplateView,
    MoreInformationTemplateView,
    PlatformCheckingView,
    PrivacyNoticeTemplateView,
)

app_name: str = "common"
urlpatterns: list[URLPattern] = [
    path("contact/", login_required(ContactAdminView.as_view()), name="contact-admin"),
    path(
        "edit-active-qa-auditor/",
        login_required(ActiveQAAuditorUpdateView.as_view()),
        name="edit-active-qa-auditor",
    ),
    path(
        "platform-versions/",
        login_required(ChangeToPlatformListView.as_view()),
        name="platform-history",
    ),
    path(
        "report-issue/", login_required(IssueReportView.as_view()), name="issue-report"
    ),
    path(
        "accessibility-statement/",
        AccessibilityStatementTemplateView.as_view(),
        name="accessibility-statement",
    ),
    path(
        "privacy-notice/",
        PrivacyNoticeTemplateView.as_view(),
        name="privacy-notice",
    ),
    path(
        "markdown-cheatsheet/",
        login_required(MarkdownCheatsheetTemplateView.as_view()),
        name="markdown-cheatsheet",
    ),
    path(
        "more-information/",
        login_required(MoreInformationTemplateView.as_view()),
        name="more-information",
    ),
    path(
        "edit-frequently-used-links/",
        login_required(FrequentlyUsedLinkFormsetTemplateView.as_view()),
        name="edit-frequently-used-links",
    ),
    path(
        "edit-footer-links/",
        login_required(FooterLinkFormsetTemplateView.as_view()),
        name="edit-footer-links",
    ),
    path(
        "metrics-case/",
        login_required(MetricsCaseTemplateView.as_view()),
        name="metrics-case",
    ),
    path(
        "metrics-policy/",
        login_required(MetricsPolicyTemplateView.as_view()),
        name="metrics-policy",
    ),
    path(
        "metrics-report/",
        login_required(MetricsReportTemplateView.as_view()),
        name="metrics-report",
    ),
    path(
        "platform-checking/",
        login_required(PlatformCheckingView.as_view()),
        name="platform-checking",
    ),
    path(
        "issue-reports-list/",
        login_required(IssueReportListView.as_view()),
        name="issue-reports-list",
    ),
    path(
        "bulk-url-search/",
        login_required(BulkURLSearchView.as_view()),
        name="bulk-url-search",
    ),
    path(
        "email-template-list/",
        login_required(EmailTemplateListView.as_view()),
        name="email-template-list",
    ),
    path(
        "<int:pk>/email-template-preview/",
        login_required(EmailTemplatePreviewDetailView.as_view()),
        name="email-template-preview",
    ),
    path(
        "email-template-create/",
        login_required(EmailTemplateCreateView.as_view()),
        name="email-template-create",
    ),
    path(
        "<int:pk>/email-template-update/",
        login_required(EmailTemplateUpdateView.as_view()),
        name="email-template-update",
    ),
]
