"""
URLS for comment section
"""

from django.urls import path
from django.contrib.auth.decorators import login_required
from accessibility_monitoring_platform.apps.comments.views import (
    CreateCaseCommentFormView,
    CommentEditView,
    CommentDeleteView,
)


app_name = "comments"
urlpatterns = [
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
