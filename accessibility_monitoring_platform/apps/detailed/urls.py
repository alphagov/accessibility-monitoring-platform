"""
URLS for cases
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from accessibility_monitoring_platform.apps.detailed.views import (
    DetailedCaseCreateView,
    DetailedCaseDetailView,
    DetailedCaseListView,
    DetailedCaseMetadataUpdateView,
)

app_name: str = "detailed"
urlpatterns: list[URLPattern] = [
    path(
        "create/",
        login_required(DetailedCaseCreateView.as_view()),
        name="case-create",
    ),
    path(
        "<int:pk>/case-detail/",
        login_required(DetailedCaseDetailView.as_view()),
        name="case-detail",
    ),
    path(
        "case-list/",
        login_required(DetailedCaseListView.as_view()),
        name="case-list",
    ),
    path(
        "<int:pk>/case-metadata/",
        login_required(DetailedCaseMetadataUpdateView.as_view()),
        name="edit-case-metadata",
    ),
]
