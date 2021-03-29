"""
URLS for dashboard
"""

from django.urls import path
from accessibility_monitoring_platform.apps.dashboard.views import home

app_name = 'dashboard'
urlpatterns = [
    path('', home, name='home'),
]
