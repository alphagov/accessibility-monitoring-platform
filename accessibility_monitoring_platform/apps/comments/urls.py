"""
URLS for comment section
"""

from django.urls import path
from django.contrib.auth.decorators import login_required
from accessibility_monitoring_platform.apps.comments.views import CommentsPostView, CommentEditView, CommentDeleteView


app_name = "comments"
urlpatterns = [
    path(
        "post-comment/",
        login_required(CommentsPostView.as_view()),
        name="post-comment"
    ),
    path(
        "<int:pk>/remove-comment/",
        login_required(CommentDeleteView.as_view()),
        name="remove-comment"
    ),
    path(
        "<int:pk>/edit-comment/",
        login_required(CommentEditView.as_view()),
        name="edit-comment"
    ),
]
