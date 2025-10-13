"""
URLS for cases
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from .views import (
    MobileCaseCreateView,
    MobileCaseDetailView,
    MobileCaseHistoryDetailView,
    MobileCaseMetadataUpdateView,
)

app_name: str = "mobile"
urlpatterns: list[URLPattern] = [
    path(
        "create/",
        login_required(MobileCaseCreateView.as_view()),
        name="case-create",
    ),
    path(
        "<int:pk>/case-detail/",
        login_required(MobileCaseDetailView.as_view()),
        name="case-detail",
    ),
    path(
        "<int:pk>/case-metadata/",
        login_required(MobileCaseMetadataUpdateView.as_view()),
        name="edit-case-metadata",
    ),
    path(
        "<int:pk>/history/",
        login_required(MobileCaseHistoryDetailView.as_view()),
        name="case-history",
    ),
]
