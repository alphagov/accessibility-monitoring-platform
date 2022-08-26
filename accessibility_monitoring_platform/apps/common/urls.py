"""
URLS for common
"""
from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern
from .views import (
    ActiveQAAuditorUpdateView,
    ContactAdminView,
    IssueReportView,
    ChangeToPlatformListView,
    AccessibilityStatementTemplateView,
    PrivacyNoticeTemplateView,
    MarkdownCheatsheetTemplateView,
)

app_name: str = "common"
urlpatterns: List[URLPattern] = [
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
        "accessibility-statement",
        AccessibilityStatementTemplateView.as_view(),
        name="accessibility-statement",
    ),
    path(
        "privacy-notice",
        PrivacyNoticeTemplateView.as_view(),
        name="privacy-notice",
    ),
    path(
        "markdown-cheatsheet",
        login_required(MarkdownCheatsheetTemplateView.as_view()),
        name="markdown-cheatsheet",
    ),
]
