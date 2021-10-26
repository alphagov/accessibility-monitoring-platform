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
    CheckListView,
    CheckUpdateView,
)

app_name: str = "checks"
urlpatterns: List[URLPattern] = [
    path("", login_required(CheckListView.as_view()), name="check-list"),
    path("create/", login_required(CheckCreateView.as_view()), name="check-create"),
    path(
        "<int:pk>/view/", login_required(CheckDetailView.as_view()), name="check-detail"
    ),
    path(
        "<int:pk>/edit-check-metadata/",
        login_required(CheckUpdateView.as_view()),
        name="edit-check-metadata",
    ),
]
