"""
URLS for cases
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from .views import (
    CaseListView,
    DocumentCreateView,
    # DocumentDeleteUpdateView,
    DocumentListView,
    DocumentUpdateView,
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
        "<int:case_id>/document-create/",
        login_required(DocumentCreateView.as_view()),
        name="document-create",
    ),
    path(
        "<int:pk>/document-update/",
        login_required(DocumentUpdateView.as_view()),
        name="document-update",
    ),
    # path(
    #     "<int:pk>/document-delete/",
    #     login_required(DocumentDeleteUpdateView.as_view()),
    #     name="document-delete",
    # ),
]
