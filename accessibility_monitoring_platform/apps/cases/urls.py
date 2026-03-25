"""
URLS for cases
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from .views import (
    CaseListView,
    DocumentUploadDeleteView,
    DocumentUploadListView,
    DocumentUploadUpdateView,
    DocumentUploadView,
    document_download,
)

app_name: str = "cases"
urlpatterns: list[URLPattern] = [
    path("", login_required(CaseListView.as_view()), name="case-list"),
    path(
        "<int:pk>/document-upload-list/",
        login_required(DocumentUploadListView.as_view()),
        name="document-upload-list",
    ),
    path(
        "<int:pk>/document-upload-create/",
        login_required(DocumentUploadView.as_view()),
        name="document-upload-create",
    ),
    path(
        "<int:pk>/document-upload-update/",
        login_required(DocumentUploadUpdateView.as_view()),
        name="document-upload-update",
    ),
    path(
        "<int:pk>/document-upload-delete/",
        login_required(DocumentUploadDeleteView.as_view()),
        name="document-upload-delete",
    ),
    path(
        "documents/<int:pk>/document-upload-download/",
        login_required(document_download),
        name="document-upload-download",
    ),
]
