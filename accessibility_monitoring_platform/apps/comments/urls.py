"""
URLS for comments
"""
from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern
from .views import QACommentUpdateView

app_name: str = "comments"
urlpatterns: List[URLPattern] = [
    path(
        "<int:pk>/edit-qa-comment/",
        login_required(QACommentUpdateView.as_view()),
        name="edit-qa-comment",
    ),
]
