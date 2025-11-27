"""
URLS for comments
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from .views import QACommentUpdateView

app_name: str = "comments"
urlpatterns: list[URLPattern] = [
    path(
        "<int:pk>/edit-qa-comment-simplified/",
        login_required(QACommentUpdateView.as_view()),
        name="edit-qa-comment-simplified",
    ),
    path(
        "<int:pk>/edit-qa-comment-detailed/",
        login_required(QACommentUpdateView.as_view()),
        name="edit-qa-comment-detailed",
    ),
    path(
        "<int:pk>/edit-qa-comment-mobile/",
        login_required(QACommentUpdateView.as_view()),
        name="edit-qa-comment-mobile",
    ),
]
