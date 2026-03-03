"""
URLS for cases
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from .views import (
    CaseListView,
    DocumentCreateView,
    DocumentListView,
    DocumentUpdateView,
    document_download,
)

app_name: str = "cases"
urlpatterns: list[URLPattern] = [
    path("", login_required(CaseListView.as_view()), name="case-list"),
    path(
        "<int:pk>/document-list/",
        login_required(DocumentListView.as_view()),
        name="document-list",
    ),
    path(
        "<int:pk>/document-create/",
        login_required(DocumentCreateView.as_view()),
        name="document-create",
    ),
    path(
        "documents/<int:pk>/document-update/",
        login_required(DocumentUpdateView.as_view()),
        name="document-update",
    ),
    path(
        "documents/<int:pk>/document-download/",
        login_required(document_download),
        name="document-download",
    ),
]
