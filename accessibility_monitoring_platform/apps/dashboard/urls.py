"""
URLS for dashboard
"""

from django.urls import path
from accessibility_monitoring_platform.apps.dashboard.views import AboutView
from django.contrib.auth.decorators import login_required


app_name = 'dashboard'
urlpatterns = [
    path('', login_required(AboutView.as_view()), name='home'),
]
