"""
URLS for dashboard
"""

from django.urls import path
from accessibility_monitoring_platform.apps.cases.views import CaseListView

app_name = 'cases'
urlpatterns = [
    path('', CaseListView.as_view(), name='cases'),
]
