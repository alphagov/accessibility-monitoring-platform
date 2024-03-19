"""
URLS for comments
"""

from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from .views import ExportCreateView, ExportListView

app_name: str = "exports"
urlpatterns: List[URLPattern] = [
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
]
