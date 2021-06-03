"""
URLS for dashboard
"""

from django.urls import path
from accessibility_monitoring_platform.apps.cases.views import (
    CaseDetailView,
    CaseListView,
    CaseWebsiteDetailUpdateView,
)

app_name = "cases"
urlpatterns = [
    path("", CaseListView.as_view(), name="case-list"),
    path("<int:pk>/view", CaseDetailView.as_view(), name="case-detail"),
    path(
        "<int:pk>/edit-website-details",
        CaseWebsiteDetailUpdateView.as_view(),
        name="edit-website-details",
    ),
    path(
        "<int:pk>/edit-contact-details",
        CaseWebsiteDetailUpdateView.as_view(),
        name="edit-contact-details",
    ),
]
