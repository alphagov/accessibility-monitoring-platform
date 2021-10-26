"""
URLS for dashboard
"""
from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern
from .views import (
    CheckCreateView,
    CheckDetailView,
    CheckMetadataUpdateView,
    CheckPagesUpdateView,
    delete_check,
    restore_check,
)

app_name: str = "checks"
urlpatterns: List[URLPattern] = [
    path("create/", login_required(CheckCreateView.as_view()), name="check-create"),
    path(
        "<int:pk>/view/", login_required(CheckDetailView.as_view()), name="check-detail"
    ),
    path(
        "<int:pk>/delete-check/",
        login_required(delete_check),
        name="delete-check",
    ),
    path(
        "<int:pk>/restore-check/",
        login_required(restore_check),
        name="restore-check",
    ),
    path(
        "<int:pk>/edit-check-metadata/",
        login_required(CheckMetadataUpdateView.as_view()),
        name="edit-check-metadata",
    ),
    path(
        "<int:pk>/edit-check-pages/",
        login_required(CheckPagesUpdateView.as_view()),
        name="edit-check-pages",
    ),
]
