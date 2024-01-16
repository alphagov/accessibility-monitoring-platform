"""
URLS for dashboard
"""

from django.contrib.auth.decorators import login_required
from django.urls import path

from accessibility_monitoring_platform.apps.dashboard.views import DashboardView

app_name = "dashboard"
urlpatterns = [
    path("", login_required(DashboardView.as_view()), name="home"),
]
