"""
URLS for common
"""
from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern
from .views import ActiveQAAuditorUpdateView

app_name: str = "common"
urlpatterns: List[URLPattern] = [
    path(
        "edit-active-qa-auditor/",
        login_required(ActiveQAAuditorUpdateView.as_view()),
        name="edit-active-qa-auditor",
    ),
]
