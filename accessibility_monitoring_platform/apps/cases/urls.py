"""
URLS for cases
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from .views import (
    CaseFileDeleteView,
    CaseFileListView,
    CaseFileUpdateView,
    CaseFileUploadView,
    CaseListView,
    case_file_download,
)

app_name: str = "cases"
urlpatterns: list[URLPattern] = [
    path("", login_required(CaseListView.as_view()), name="case-list"),
    path(
        "<int:pk>/case-file-list/",
        login_required(CaseFileListView.as_view()),
        name="case-file-list",
    ),
    path(
        "<int:pk>/case-file-create/",
        login_required(CaseFileUploadView.as_view()),
        name="case-file-create",
    ),
    path(
        "<int:pk>/case-file-update/",
        login_required(CaseFileUpdateView.as_view()),
        name="case-file-update",
    ),
    path(
        "<int:pk>/case-file-delete/",
        login_required(CaseFileDeleteView.as_view()),
        name="case-file-delete",
    ),
    path(
        "documents/<int:pk>/case-file-download/",
        login_required(case_file_download),
        name="case-file-download",
    ),
]
