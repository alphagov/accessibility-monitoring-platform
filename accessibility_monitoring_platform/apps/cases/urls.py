"""
URLS for cases
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from .views import CaseListView

app_name: str = "cases"
urlpatterns: list[URLPattern] = [
    path("", login_required(CaseListView.as_view()), name="case-list"),
]
