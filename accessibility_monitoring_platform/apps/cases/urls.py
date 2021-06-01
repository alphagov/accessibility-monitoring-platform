"""
URLS for dashboard
"""

from django.urls import path
from accessibility_monitoring_platform.apps.cases.views import CaseDetailView, CaseListView

app_name = "cases"
urlpatterns = [
    path("", CaseListView.as_view(), name="case-list"),
    path("<int:pk>/view", CaseDetailView.as_view(), name="case-detail"),
]
