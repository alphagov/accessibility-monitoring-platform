"""
URLS for comment section
"""

from django.urls import path
from django.contrib.auth.decorators import login_required
from accessibility_monitoring_platform.apps.comments.views import (
    CommentCreateView,
    CommentUpdateView,
    CreateCaseCommentFormView,
    CommentEditView,
    CommentDeleteView,
)


app_name = "comments"
urlpatterns = [
    path(
        "<int:case_id>/create-comment/",
        login_required(CommentCreateView.as_view()),
        name="create-comment",
    ),
    path(
        "<int:pk>/update-comment/",
        login_required(CommentUpdateView.as_view()),
        name="update-comment",
    ),
    path(
        "<int:case_id>/create-case-comment/",
        login_required(CreateCaseCommentFormView.as_view()),
        name="create-case-comment",
    ),
    path(
        "<int:pk>/remove-comment/",
        login_required(CommentDeleteView.as_view()),
        name="remove-comment",
    ),
    path(
        "<int:pk>/edit-comment/",
        login_required(CommentEditView.as_view()),
        name="edit-comment",
    ),
]
